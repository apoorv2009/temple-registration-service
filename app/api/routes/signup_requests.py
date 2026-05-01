from datetime import date

import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.schemas.signup_request import (
    DonationCreateRequest,
    DonationListResponse,
    DonationResponse,
    RejectTempleSubscriptionPayload,
    ShantidharaBookingCreateRequest,
    ShantidharaBookingListResponse,
    ShantidharaBookingResponse,
    TempleSubscriptionCreateRequest,
    TempleSubscriptionListResponse,
    TempleSubscriptionResponse,
)
from app.services.signup_requests import temple_subscription_store

router = APIRouter()


async def _get_active_temple_or_raise(temple_id: str) -> dict[str, object]:
    settings = get_settings()
    url = f"{settings.admin_service_url}/api/v1/temples/{temple_id}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to validate temple status",
        ) from exc

    if response.status_code == 404:
        raise HTTPException(status_code=400, detail="Temple is not onboarded")

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Temple service returned an unexpected error",
        )

    temple = response.json()
    if temple.get("status") != "active":
        raise HTTPException(status_code=400, detail="Temple is not active")

    return temple


async def _get_shantidhara_slot_or_raise(
    temple_id: str,
    slot_id: str,
) -> dict[str, object]:
    settings = get_settings()
    url = f"{settings.admin_service_url}/api/v1/temples/{temple_id}/shantidhara/slots"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to validate Shantidhara slot",
        ) from exc

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Temple service returned an unexpected error",
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Temple slot information is unavailable")

    body = response.json()
    for item in body.get("items", []):
        if item.get("slot_id") == slot_id:
            if item.get("status") != "available":
                raise HTTPException(status_code=409, detail="Selected Shantidhara slot is not available")
            return item

    raise HTTPException(status_code=404, detail="Selected Shantidhara slot was not found")


@router.post("", response_model=TempleSubscriptionResponse)
async def create_temple_subscription(
    payload: TempleSubscriptionCreateRequest,
) -> TempleSubscriptionResponse:
    temple = await _get_active_temple_or_raise(payload.temple_id)
    try:
        return temple_subscription_store.create(
            user_id=payload.user_id,
            temple_id=payload.temple_id,
            temple_name=str(temple["temple_name"]),
            requester_name=payload.requester_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/me", response_model=TempleSubscriptionListResponse)
async def list_my_temple_subscriptions(
    user_id: str = Query(..., min_length=3),
) -> TempleSubscriptionListResponse:
    return TempleSubscriptionListResponse(items=temple_subscription_store.list_for_user(user_id))


@router.get("/admin/list", response_model=TempleSubscriptionListResponse)
async def list_temple_subscriptions_for_admin(
    temple_id: str = Query(..., min_length=3),
    status_filter: str | None = Query(default="pending"),
) -> TempleSubscriptionListResponse:
    return TempleSubscriptionListResponse(
        items=temple_subscription_store.list_for_temple(temple_id, status_filter=status_filter),
    )


@router.post("/admin/{subscription_id}/approve")
async def approve_temple_subscription(subscription_id: str) -> dict[str, object]:
    try:
        item = temple_subscription_store.approve(subscription_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if item is None:
        raise HTTPException(status_code=404, detail="Temple subscription not found")
    return item.model_dump()


@router.post("/admin/{subscription_id}/reject")
async def reject_temple_subscription(
    subscription_id: str,
    payload: RejectTempleSubscriptionPayload,
) -> dict[str, object]:
    try:
        item = temple_subscription_store.reject(subscription_id, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if item is None:
        raise HTTPException(status_code=404, detail="Temple subscription not found")
    return item.model_dump()


@router.post("/shantidhara-bookings", response_model=ShantidharaBookingResponse)
async def create_shantidhara_booking(
    payload: ShantidharaBookingCreateRequest,
) -> ShantidharaBookingResponse:
    temple = await _get_active_temple_or_raise(payload.temple_id)
    slot = await _get_shantidhara_slot_or_raise(payload.temple_id, payload.slot_id)
    try:
        return temple_subscription_store.create_shantidhara_booking(
            user_id=payload.user_id,
            temple_id=payload.temple_id,
            temple_name=str(temple["temple_name"]),
            slot_id=payload.slot_id,
            slot_label=str(slot["slot_label"]),
            slot_date=date.fromisoformat(str(slot["slot_date"])),
            amount_label=str(slot["amount_label"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/shantidhara-bookings/me", response_model=ShantidharaBookingListResponse)
async def list_my_shantidhara_bookings(
    user_id: str = Query(..., min_length=3),
    temple_id: str | None = Query(default=None),
) -> ShantidharaBookingListResponse:
    return ShantidharaBookingListResponse(
        items=temple_subscription_store.list_shantidhara_bookings(user_id=user_id, temple_id=temple_id),
    )


@router.post("/donations", response_model=DonationResponse)
async def create_donation(payload: DonationCreateRequest) -> DonationResponse:
    temple = await _get_active_temple_or_raise(payload.temple_id)
    return temple_subscription_store.create_donation(
        user_id=payload.user_id,
        temple_id=payload.temple_id,
        temple_name=str(temple["temple_name"]),
        donation_type=payload.donation_type,
        amount_label=payload.amount_label,
    )


@router.get("/donations/me", response_model=DonationListResponse)
async def list_my_donations(
    user_id: str = Query(..., min_length=3),
    temple_id: str | None = Query(default=None),
) -> DonationListResponse:
    return DonationListResponse(
        items=temple_subscription_store.list_donations(user_id=user_id, temple_id=temple_id),
    )

import httpx
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.schemas.signup_request import (
    RejectTempleSubscriptionPayload,
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

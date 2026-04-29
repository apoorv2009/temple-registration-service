from fastapi import APIRouter

from app.schemas.signup_request import (
    ReferredSignupRequest,
    SelfSignupRequest,
    SignupRequestResponse,
)

router = APIRouter()


@router.post("/self", response_model=SignupRequestResponse)
async def create_self_signup_request(
    payload: SelfSignupRequest,
) -> SignupRequestResponse:
    return SignupRequestResponse(
        request_id=f"self-{payload.contact_number}",
        status="pending",
        request_type=payload.request_type,
    )


@router.post("/referred", response_model=SignupRequestResponse)
async def create_referred_signup_request(
    payload: ReferredSignupRequest,
) -> SignupRequestResponse:
    return SignupRequestResponse(
        request_id=f"referred-{payload.contact_number}",
        status="pending",
        request_type=payload.request_type,
    )


@router.get("/{request_id}")
async def get_signup_request(request_id: str) -> dict[str, str]:
    return {"request_id": request_id, "status": "pending", "phase": "scaffold"}


from typing import Literal

from pydantic import BaseModel, Field


class BaseSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    contact_number: str = Field(..., min_length=10, max_length=20)
    native_city: str = Field(..., min_length=2, max_length=100)
    local_area: str = Field(..., min_length=2, max_length=100)
    occupation: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class SelfSignupRequest(BaseSignupRequest):
    request_type: Literal["self_service"] = "self_service"


class ReferredSignupRequest(BaseSignupRequest):
    request_type: Literal["referred"] = "referred"
    requested_by_user_id: str = Field(..., min_length=3, max_length=64)


class SignupRequestResponse(BaseModel):
    request_id: str
    status: Literal["pending"]
    request_type: Literal["self_service", "referred"]
    phase: str = "scaffold"


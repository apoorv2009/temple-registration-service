from fastapi import APIRouter

from app.api.routes import health, signup_requests

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(
    signup_requests.router,
    prefix="/api/v1/signup-requests",
    tags=["signup-requests"],
)


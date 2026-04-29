from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="Temple Registration Service",
    version="0.1.0",
    summary="Signup request management service for devotee onboarding.",
)
app.include_router(api_router)


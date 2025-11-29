"""Health check endpoint."""

from fastapi import APIRouter
from app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with status and version
    """
    return HealthResponse(status="healthy", version="1.0.0")

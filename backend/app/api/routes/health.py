"""HTTP routes for basic application health checks."""

from fastapi import APIRouter, Depends  # type: ignore

from app.schemas.health import HealthStatus
from app.services.health import HealthService, get_health_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
def health_check(service: HealthService = Depends(get_health_service)) -> HealthStatus:
    """Return the API health response."""
    return service.get_status()

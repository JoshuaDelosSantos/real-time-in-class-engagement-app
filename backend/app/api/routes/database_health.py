"""HTTP routes that exercise database connectivity."""

from fastapi import APIRouter, Depends  # type: ignore

from app.schemas.health import DatabasePingResult
from app.services.database_health import (
    DatabaseHealthService,
    get_database_health_service,
)

router = APIRouter(prefix="/db", tags=["database"])


@router.post("/ping", response_model=DatabasePingResult)
def db_ping(
    service: DatabaseHealthService = Depends(get_database_health_service),
) -> DatabasePingResult:
    """Insert a ping row and return aggregate counts."""
    return service.record_ping()

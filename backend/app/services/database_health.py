"""Service functions for exercising and reporting database health."""

from app.repositories.health_checks import HealthCheckRepository
from app.schemas.health import DatabasePingResult


class DatabaseHealthService:
    """Coordinate database health checks via the repository layer."""

    def __init__(self, repository: HealthCheckRepository | None = None) -> None:
        self._repository = repository or HealthCheckRepository()

    def record_ping(self) -> DatabasePingResult:
        """Insert a ping record and report insertion metadata."""
        inserted_id, total_rows = self._repository.record_ping()
        return DatabasePingResult(inserted_id=inserted_id, total_rows=total_rows)


def get_database_health_service() -> DatabaseHealthService:
    """FastAPI dependency hook returning a database health service instance."""
    return DatabaseHealthService()

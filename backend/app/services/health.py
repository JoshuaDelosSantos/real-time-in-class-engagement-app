"""Service helpers for general API health checks."""

from app.schemas.health import HealthStatus


class HealthService:
    """Provide basic API health metadata."""

    def __init__(self, message: str = "Hello World!") -> None:
        self._message = message

    def get_status(self) -> HealthStatus:
        """Return the current API health summary."""
        return HealthStatus(status="ok", message=self._message)


def get_health_service() -> HealthService:
    """FastAPI dependency hook for the health service."""
    return HealthService()

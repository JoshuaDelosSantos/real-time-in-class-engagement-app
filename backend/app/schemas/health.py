"""Pydantic models describing health-related responses."""

from pydantic import BaseModel # type: ignore


class HealthStatus(BaseModel):
    """Response body for the API health endpoint."""

    status: str
    message: str


class DatabasePingResult(BaseModel):
    """Response body produced when the database ping endpoint executes."""

    inserted_id: int
    total_rows: int

"""FastAPI router exposing session endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status # type: ignore

from app.schemas.sessions import SessionCreate, SessionSummary
from app.services import (
    HostSessionLimitError,
    InvalidHostDisplayNameError,
    SessionCodeCollisionError,
    get_session_service,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate) -> SessionSummary:
    """Create a session and return summary details."""

    service = get_session_service()
    try:
        return service.create_session(
            title=payload.title,
            host_display_name=payload.host_display_name,
        )
    except InvalidHostDisplayNameError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except HostSessionLimitError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SessionCodeCollisionError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    limit: Annotated[int | None, Query(description="Maximum number of sessions to return", ge=1)] = 10,
) -> list[SessionSummary]:
    """Retrieve recent joinable sessions.
    
    Returns sessions ordered by creation time (most recent first).
    Only includes draft and active sessions.
    """

    service = get_session_service()
    return service.get_recent_sessions(limit=limit)

"""Pydantic models for session entities."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field # type: ignore

from .users import UserSummary


SessionStatus = Literal["draft", "active", "ended"]


class SessionBase(BaseModel):
    """Shared attributes for session schemas."""

    title: str = Field(..., min_length=1, max_length=200)


class SessionCreate(SessionBase):
    """Schema for creating a new session.

    The `host_display_name` field is provided by clients, while the
    service layer is responsible for locating or creating the
    corresponding `users` row before persisting the session.
    """

    host_display_name: Optional[str] = Field(None, min_length=1, max_length=100)


class SessionRead(SessionBase):
    """Schema for reading complete session data from the database.

    Includes the full host object for richer API responses.
    """

    id: int
    code: str
    status: SessionStatus
    host: "UserSummary"
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SessionSummary(BaseModel):
    """Lightweight session summary for API responses.

    Includes host details to avoid additional requests.
    """

    id: int
    code: str
    title: str
    status: SessionStatus
    host: "UserSummary"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionUpdate(BaseModel):
    """Schema for updating session attributes.
    
    All fields are optional to support partial updates.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[SessionStatus] = None


class SessionJoin(BaseModel):
    """Schema for joining a session via code."""

    code: str = Field(..., min_length=1, max_length=10)
    display_name: str = Field(..., min_length=1, max_length=100)

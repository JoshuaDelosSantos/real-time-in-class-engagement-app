"""Pydantic models for session participant entities."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict # type: ignore

from .users import UserSummary


ParticipantRole = Literal["host", "participant"]


class SessionParticipantBase(BaseModel):
    """Shared attributes for participant schemas."""

    role: ParticipantRole


class SessionParticipantCreate(SessionParticipantBase):
    """Schema for creating a participant record.

    Intended for internal service use; route handlers gather `session_id`
    from path params while services resolve `user_id` after creating or
    locating a user record.
    """

    session_id: int
    user_id: int


class SessionParticipantRead(SessionParticipantBase):
    """Schema for reading participant data from the database.

    Includes full user details for roster displays.
    """

    id: int
    session_id: int
    user: "UserSummary"
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionParticipantSummary(BaseModel):
    """Lightweight participant summary for API responses.

    Embeds user details to support participant lists without extra queries.
    """

    user: "UserSummary"
    role: ParticipantRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

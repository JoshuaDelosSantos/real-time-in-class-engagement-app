"""Pydantic models for question entities."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field # type: ignore

from .users import UserSummary


QuestionStatus = Literal["pending", "answered"]


class QuestionBase(BaseModel):
    """Shared attributes for question schemas."""

    body: str = Field(..., min_length=1, max_length=280)


class QuestionCreate(QuestionBase):
    """Schema for submitting a new question.

    The author identity is captured from session context; this schema is
    exposed publicly but intentionally excludes author identifiers.
    """


class QuestionRead(QuestionBase):
    """Schema for reading complete question data from the database.
    
    Includes optional author details for attributed questions.
    """

    id: int
    session_id: int
    author: Optional["UserSummary"]
    status: QuestionStatus
    likes: int
    created_at: datetime
    answered_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class QuestionSummary(BaseModel):
    """Lightweight question summary for API responses.

    Includes optional author details and session identifier to avoid
    additional lookups when rendering lists.
    """

    id: int
    session_id: int
    body: str
    status: QuestionStatus
    likes: int
    author: Optional["UserSummary"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionUpdate(BaseModel):
    """Schema for updating question attributes.
    
    Primarily used by moderators to mark questions as answered.
    """

    status: Optional[QuestionStatus] = None

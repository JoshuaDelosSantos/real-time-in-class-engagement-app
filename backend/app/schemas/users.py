"""Pydantic models for user entities."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field # type: ignore


class UserBase(BaseModel):
    """Shared attributes for user schemas."""

    display_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserRead(UserBase):
    """Schema for reading user data from the database."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    """Lightweight user summary for nested responses."""

    id: int
    display_name: str

    model_config = ConfigDict(from_attributes=True)

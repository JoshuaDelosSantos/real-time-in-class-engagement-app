"""Pydantic models for question vote entities."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict # type: ignore


class QuestionVoteCreate(BaseModel):
    """Schema for recording a vote on a question.

    Services construct this internally using route parameters and
    authenticated user context; external callers should not supply
    these identifiers directly.
    """

    question_id: int
    voter_user_id: int


class QuestionVoteRead(BaseModel):
    """Schema for reading vote data from the database."""

    id: int
    question_id: int
    voter_user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionVoteSummary(BaseModel):
    """Lightweight vote summary for API responses."""

    question_id: int
    voter_user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoteToggleResult(BaseModel):
    """Response schema for vote toggle operations.
    
    Indicates whether a vote was added or removed.
    """

    question_id: int
    liked: bool
    total_likes: int

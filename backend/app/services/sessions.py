"""Business workflows for session creation and management."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import Protocol

import psycopg # type: ignore

from app.db import db_connection
from app.repositories import (
    add_participant,
    count_active_sessions_for_host,
    count_user_pending_questions,
    create_question,
    create_user,
    get_participant,
    get_session_by_code,
    get_user_by_display_name,
    get_user_by_id,
    insert_session,
    list_session_participants,
    list_session_questions,
    list_sessions,
)
from app.schemas.sessions import SessionSummary
from app.schemas.session_participants import SessionParticipantSummary
from app.schemas.questions import QuestionSummary
from app.schemas.users import UserSummary


DEFAULT_CODE_LENGTH = 6
MAX_SESSION_CODE_ATTEMPTS = 10
HOST_SESSION_LIMIT = 3


class SessionCreationError(RuntimeError):
    """Base class for session creation failures."""


class HostSessionLimitError(SessionCreationError):
    """Raised when a host has reached the allowed number of active sessions."""


class SessionCodeCollisionError(SessionCreationError):
    """Raised when we cannot generate a unique join code after several attempts."""


class InvalidHostDisplayNameError(SessionCreationError):
    """Raised when the provided host display name is empty."""


class SessionNotFoundError(RuntimeError):
    """Raised when a session code doesn't match any session."""


class SessionNotJoinableError(RuntimeError):
    """Raised when attempting to join a session that has ended."""


class NotParticipantError(RuntimeError):
    """Raised when a user attempts to perform an action but is not a participant in the session."""


class QuestionLimitExceededError(RuntimeError):
    """Raised when a user has reached the maximum number of pending questions allowed."""


class ConnectionProvider(Protocol):
    """Protocol for objects that provide psycopg connections."""

    def __call__(self) -> psycopg.Connection:  # pragma: no cover - interface definition
        ...


@dataclass
class SessionService:
    """Encapsulates session-related business workflows."""

    connection_provider: ConnectionProvider = db_connection

    def create_session(self, *, title: str, host_display_name: str | None) -> SessionSummary:
        """Create a new session and return its summary."""

        if not host_display_name or not host_display_name.strip():
            raise InvalidHostDisplayNameError("Host display name is required")

        clean_display_name = host_display_name.strip()

        with self.connection_provider() as conn:
            host = self._get_or_create_user(conn, clean_display_name)

            if self._host_has_reached_limit(conn, host_id=host["id"]):
                raise HostSessionLimitError(
                    "Host has reached the maximum number of active sessions"
                )

            join_code = self._generate_unique_code(conn)
            session = insert_session(
                conn,
                host_user_id=host["id"],
                title=title,
                code=join_code,
            )

            add_participant(
                conn,
                session_id=session["id"],
                user_id=host["id"],
                role="host",
            )

        return SessionSummary(
            id=session["id"],
            code=session["code"],
            title=session["title"],
            status=session["status"],
            host=UserSummary(id=host["id"], display_name=host["display_name"]),
            created_at=session["created_at"],
        )

    @staticmethod
    def _get_or_create_user(conn: psycopg.Connection, display_name: str) -> dict:
        """Get existing user by display name or create a new one."""
        existing = get_user_by_display_name(conn, display_name)
        if existing:
            return existing
        return create_user(conn, display_name)

    @staticmethod
    def _host_has_reached_limit(conn: psycopg.Connection, host_id: int) -> bool:
        active_count = count_active_sessions_for_host(conn, host_id)
        return active_count >= HOST_SESSION_LIMIT

    @staticmethod
    def _generate_unique_code(conn: psycopg.Connection) -> str:
        for _ in range(MAX_SESSION_CODE_ATTEMPTS):
            code = _generate_join_code()
            if not get_session_by_code(conn, code):
                return code
        raise SessionCodeCollisionError("Failed to generate a unique join code")

    def get_recent_sessions(self, *, limit: int | None = None) -> list[SessionSummary]:
        """Retrieve recent joinable sessions with host information.
        
        Returns sessions in descending order by creation time (most recent first).
        Only includes draft and active sessions.
        """

        with self.connection_provider() as conn:
            session_rows = list_sessions(conn, limit=limit)
            
            # Build unique set of host IDs and fetch host data
            host_ids = {row["host_user_id"] for row in session_rows}
            host_map = {}
            for host_id in host_ids:
                host = get_user_by_id(conn, host_id)
                if host:
                    host_map[host_id] = UserSummary(
                        id=host["id"],
                        display_name=host["display_name"]
                    )
            
            # Map session rows to SessionSummary with host data
            return [
                SessionSummary(
                    id=row["id"],
                    code=row["code"],
                    title=row["title"],
                    status=row["status"],
                    host=host_map[row["host_user_id"]],
                    created_at=row["created_at"],
                )
                for row in session_rows
            ]

    def get_session_details(self, *, code: str) -> SessionSummary:
        """Retrieve session details by join code.
        
        Args:
            code: The session join code
            
        Returns:
            SessionSummary with session and host details
            
        Raises:
            SessionNotFoundError: Session code doesn't exist
        """
        with self.connection_provider() as conn:
            # Look up session by code
            session = get_session_by_code(conn, code)
            if not session:
                raise SessionNotFoundError("Session not found")
            
            # Fetch host details for response
            host = get_user_by_id(conn, session["host_user_id"])
        
        return SessionSummary(
            id=session["id"],
            code=session["code"],
            title=session["title"],
            status=session["status"],
            host=UserSummary(id=host["id"], display_name=host["display_name"]),
            created_at=session["created_at"],
        )

    def get_session_participants(self, *, code: str) -> list[SessionParticipantSummary]:
        """Retrieve participant roster for a session.
        
        Args:
            code: The session join code
            
        Returns:
            List of SessionParticipantSummary with participant and user details
            
        Raises:
            SessionNotFoundError: Session code doesn't exist
        """
        with self.connection_provider() as conn:
            # Look up session by code
            session = get_session_by_code(conn, code)
            if not session:
                raise SessionNotFoundError("Session not found")
            
            # Fetch participant records
            participant_rows = list_session_participants(conn, session["id"])
        
        # Map to SessionParticipantSummary with embedded UserSummary
        return [
            SessionParticipantSummary(
                user=UserSummary(
                    id=row["user_id"],
                    display_name=row["display_name"]
                ),
                role=row["role"],
                joined_at=row["joined_at"],
            )
            for row in participant_rows
        ]

    def get_session_questions(
        self,
        *,
        code: str,
        status: str | None = None,
    ) -> list[QuestionSummary]:
        """Retrieve questions for a session.
        
        Args:
            code: The session join code
            status: Optional status filter ("pending" or "answered")
            
        Returns:
            List of QuestionSummary with question and author details
            
        Raises:
            SessionNotFoundError: Session code doesn't exist
        """
        with self.connection_provider() as conn:
            # Look up session by code
            session = get_session_by_code(conn, code)
            if not session:
                raise SessionNotFoundError("Session not found")
            
            # Fetch question records
            question_rows = list_session_questions(conn, session["id"], status_filter=status)
        
        # Map to QuestionSummary with embedded UserSummary (or None for anonymous)
        return [
            QuestionSummary(
                id=row["id"],
                session_id=row["session_id"],
                body=row["body"],
                status=row["status"],
                likes=row["likes"],
                author=(
                    UserSummary(
                        id=row["author_user_id"],
                        display_name=row["author_display_name"]
                    )
                    if row["author_user_id"] is not None
                    else None
                ),
                created_at=row["created_at"],
            )
            for row in question_rows
        ]

    def join_session(self, *, code: str, display_name: str) -> SessionSummary:
        """Join a session using a code and display name.
        
        Creates a participant record linking the user to the session.
        Returns session details for the participant.
        
        Args:
            code: The session join code
            display_name: The participant's display name
            
        Returns:
            SessionSummary with session and host details
            
        Raises:
            InvalidHostDisplayNameError: Display name is empty or whitespace-only
            SessionNotFoundError: Session code doesn't exist
            SessionNotJoinableError: Session status is 'ended'
        """
        # Validate display name
        if not display_name or not display_name.strip():
            raise InvalidHostDisplayNameError("Display name is required")
        
        clean_display_name = display_name.strip()
        
        with self.connection_provider() as conn:
            # Look up session by code
            session = get_session_by_code(conn, code)
            if not session:
                raise SessionNotFoundError("Session not found")
            
            # Verify session is joinable (not ended)
            if session["status"] == "ended":
                raise SessionNotJoinableError("Session has ended and is no longer joinable")
            
            # Get or create user
            user = self._get_or_create_user(conn, clean_display_name)
            
            # CRITICAL: Determine role - preserve host role if user is the session host
            if user["id"] == session["host_user_id"]:
                role = "host"
            else:
                role = "participant"
            
            # Add participant record (idempotent due to ON CONFLICT)
            add_participant(
                conn,
                session_id=session["id"],
                user_id=user["id"],
                role=role,
            )
            
            # Fetch host details for response
            host = get_user_by_id(conn, session["host_user_id"])
        
        return SessionSummary(
            id=session["id"],
            code=session["code"],
            title=session["title"],
            status=session["status"],
            host=UserSummary(id=host["id"], display_name=host["display_name"]),
            created_at=session["created_at"],
        )

    def submit_question(self, *, code: str, user_id: int, body: str) -> QuestionSummary:
        """Submit a new question to a session.
        
        Args:
            code: The session join code
            user_id: ID of the user submitting the question
            body: Question text content
            
        Returns:
            QuestionSummary with the created question and author details
            
        Raises:
            SessionNotFoundError: Session code doesn't exist
            SessionNotJoinableError: Session status is 'ended'
            NotParticipantError: User is not a participant in the session
            QuestionLimitExceededError: User has reached the 3-question limit
        """
        # Validate and clean body
        if not body or not body.strip():
            raise ValueError("Question body cannot be empty")
        
        clean_body = body.strip()
        
        if len(clean_body) > 280:
            raise ValueError("Question exceeds 280 characters")
        
        with self.connection_provider() as conn:
            # Look up session by code
            session = get_session_by_code(conn, code)
            if not session:
                raise SessionNotFoundError("Session not found")
            
            # Verify session is active or draft (not ended)
            if session["status"] == "ended":
                raise SessionNotJoinableError("Session has ended and is no longer accepting questions")
            
            # Verify user is a participant
            participant = get_participant(conn, session["id"], user_id)
            if not participant:
                raise NotParticipantError("User must be a participant to submit questions")
            
            # Get user details for author attribution
            user = get_user_by_id(conn, user_id)
            if not user:
                raise NotParticipantError("User not found")
            
            # Count user's pending questions
            pending_count = count_user_pending_questions(conn, session["id"], user_id)
            
            # TODO: Race condition possible with autocommit connections.
            # Count + insert not atomic. Two concurrent submissions may exceed limit.
            # Fix: Wrap in transaction with SELECT FOR UPDATE when migrating away from autocommit.
            # Risk: Low (requires exact concurrent timing from same user).
            # Mitigation: Client-side button disabling reduces likelihood.
            if pending_count >= 3:
                raise QuestionLimitExceededError("User has reached the maximum of 3 pending questions")
            
            # Create the question
            question = create_question(
                conn,
                session_id=session["id"],
                author_user_id=user_id,
                body=clean_body,
            )
        
        # Build and return QuestionSummary
        return QuestionSummary(
            id=question["id"],
            session_id=question["session_id"],
            body=question["body"],
            status=question["status"],
            likes=question["likes"],
            author=UserSummary(id=user["id"], display_name=user["display_name"]),
            created_at=question["created_at"],
        )


def _generate_join_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    characters = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


def get_session_service() -> SessionService:
    """FastAPI-friendly dependency getter."""

    return SessionService()

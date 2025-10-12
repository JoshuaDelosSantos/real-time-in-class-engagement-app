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
    create_user,
    get_session_by_code,
    get_user_by_display_name,
    insert_session,
)
from app.schemas.sessions import SessionSummary
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
            host = self._get_or_create_host(conn, clean_display_name)

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
    def _get_or_create_host(conn: psycopg.Connection, display_name: str) -> dict:
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


def _generate_join_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    characters = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


def get_session_service() -> SessionService:
    """FastAPI-friendly dependency getter."""

    return SessionService()

from __future__ import annotations

import psycopg # type: ignore
import pytest # type: ignore

from app.repositories import create_user, insert_session
from app.schemas.sessions import SessionSummary
from app.services.sessions import (
    HOST_SESSION_LIMIT,
    HostSessionLimitError,
    InvalidHostDisplayNameError,
    SessionService,
)
from app.settings import get_psycopg_dsn


def _connection_provider():
    dsn = get_psycopg_dsn()

    def factory():
        return psycopg.connect(dsn, autocommit=True)

    return factory


def test_create_session_creates_host_and_participant() -> None:
    service = SessionService(connection_provider=_connection_provider())

    summary = service.create_session(title="Biology", host_display_name="Dr. Willow")

    assert isinstance(summary, SessionSummary)
    assert summary.title == "Biology"
    assert summary.host.display_name == "Dr. Willow"


def test_create_session_rejects_empty_host_name() -> None:
    service = SessionService(connection_provider=_connection_provider())

    with pytest.raises(InvalidHostDisplayNameError):
        service.create_session(title="Physics", host_display_name="  ")


def test_session_limit_enforced() -> None:
    service = SessionService(connection_provider=_connection_provider())

    for index in range(HOST_SESSION_LIMIT):
        service.create_session(title=f"Session {index}", host_display_name="Dr. Limit")

    with pytest.raises(HostSessionLimitError):
        service.create_session(title="Overflow", host_display_name="Dr. Limit")


def test_generate_unique_code_handles_collisions(monkeypatch) -> None:
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        host = create_user(conn, "Dr. Existing")
        insert_session(conn, host_user_id=host["id"], title="Existing", code="DUPLIC")

    service = SessionService(connection_provider=_connection_provider())

    codes = ["DUPLIC", "UNIQUE1"]

    def fake_generate(length: int = 6) -> str:
        return codes.pop(0)

    monkeypatch.setattr("app.services.sessions._generate_join_code", fake_generate)

    summary = service.create_session(title="New", host_display_name="Dr. Existing")
    assert summary.code == "UNIQUE1"

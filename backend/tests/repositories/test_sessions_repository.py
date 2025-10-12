from __future__ import annotations

from app.repositories import (
    count_active_sessions_for_host,
    create_user,
    get_session_by_code,
    insert_session,
)


def test_insert_session_persists_and_returns_row(db_connection) -> None:
    host = create_user(db_connection, "Dr. Host")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Chemistry 101",
        code="ABC123",
    )

    assert session["title"] == "Chemistry 101"
    assert session["status"] == "draft"

    fetched = get_session_by_code(db_connection, "ABC123")
    assert fetched is not None
    assert fetched["id"] == session["id"]


def test_count_active_sessions_excludes_ended(db_connection) -> None:
    host = create_user(db_connection, "Dr. Host")

    insert_session(db_connection, host_user_id=host["id"], title="Math", code="CODE01")
    insert_session(
        db_connection,
        host_user_id=host["id"],
        title="History",
        code="CODE02",
        status="ended",
    )

    active = count_active_sessions_for_host(db_connection, host["id"])
    assert active == 1


def test_get_session_by_code_returns_none_for_missing(db_connection) -> None:
    assert get_session_by_code(db_connection, "MISSING") is None

from __future__ import annotations

from app.repositories import (
    count_active_sessions_for_host,
    create_user,
    get_session_by_code,
    insert_session,
    list_sessions,
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


def test_list_sessions_returns_recent_first(db_connection) -> None:
    host = create_user(db_connection, "Prof. Sessions")

    session1 = insert_session(
        db_connection, host_user_id=host["id"], title="First", code="CODE01"
    )
    session2 = insert_session(
        db_connection, host_user_id=host["id"], title="Second", code="CODE02"
    )

    sessions = list_sessions(db_connection)
    assert len(sessions) == 2
    assert sessions[0]["id"] == session2["id"]  # most recent first
    assert sessions[1]["id"] == session1["id"]


def test_list_sessions_respects_limit(db_connection) -> None:
    host = create_user(db_connection, "Prof. Limiter")

    for i in range(5):
        insert_session(
            db_connection, host_user_id=host["id"], title=f"Session {i}", code=f"CODE{i}"
        )

    sessions = list_sessions(db_connection, limit=2)
    assert len(sessions) == 2


def test_list_sessions_filters_ended_status(db_connection) -> None:
    host = create_user(db_connection, "Prof. Filter")

    insert_session(
        db_connection, host_user_id=host["id"], title="Draft", code="DRAFT1"
    )
    insert_session(
        db_connection, host_user_id=host["id"], title="Active", code="ACTIVE1", status="active"
    )
    insert_session(
        db_connection, host_user_id=host["id"], title="Ended", code="ENDED1", status="ended"
    )

    sessions = list_sessions(db_connection)
    assert len(sessions) == 2
    assert all(s["status"] in ("draft", "active") for s in sessions)


def test_list_sessions_returns_empty_when_none_available(db_connection) -> None:
    sessions = list_sessions(db_connection)
    assert sessions == []

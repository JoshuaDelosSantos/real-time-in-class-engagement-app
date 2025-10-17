from __future__ import annotations

import psycopg # type: ignore
import pytest # type: ignore

from app.repositories import create_user, get_participant, insert_session
from app.schemas.sessions import SessionSummary
from app.services.sessions import (
    HOST_SESSION_LIMIT,
    HostSessionLimitError,
    InvalidHostDisplayNameError,
    SessionNotFoundError,
    SessionNotJoinableError,
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


def test_get_recent_sessions_returns_summaries_with_hosts() -> None:
    service = SessionService(connection_provider=_connection_provider())

    session1 = service.create_session(title="Math 101", host_display_name="Prof. Alpha")
    session2 = service.create_session(title="History 202", host_display_name="Prof. Beta")

    sessions = service.get_recent_sessions()

    assert len(sessions) == 2
    assert all(isinstance(s, SessionSummary) for s in sessions)
    # Most recent first
    assert sessions[0].id == session2.id
    assert sessions[0].host.display_name == "Prof. Beta"
    assert sessions[1].id == session1.id
    assert sessions[1].host.display_name == "Prof. Alpha"


def test_get_recent_sessions_respects_limit() -> None:
    service = SessionService(connection_provider=_connection_provider())

    for i in range(5):
        service.create_session(title=f"Session {i}", host_display_name=f"Host {i}")

    sessions = service.get_recent_sessions(limit=3)
    assert len(sessions) == 3


def test_get_recent_sessions_returns_empty_when_none_exist() -> None:
    service = SessionService(connection_provider=_connection_provider())

    sessions = service.get_recent_sessions()
    assert sessions == []


# Join Session Tests


def test_join_session_with_new_user() -> None:
    """Test joining a session creates new user and participant record."""
    
    service = SessionService(connection_provider=_connection_provider())
    
    # Create a session
    session = service.create_session(title="Biology 101", host_display_name="Dr. Smith")
    
    # Join with a new user
    result = service.join_session(code=session.code, display_name="Student Alice")
    
    assert isinstance(result, SessionSummary)
    assert result.id == session.id
    assert result.code == session.code
    assert result.title == "Biology 101"
    assert result.host.display_name == "Dr. Smith"


def test_join_session_with_existing_user() -> None:
    """Test joining a session reuses existing user record."""
    
    dsn = get_psycopg_dsn()
    service = SessionService(connection_provider=_connection_provider())
    
    # Create user directly in DB
    with psycopg.connect(dsn, autocommit=True) as conn:
        existing_user = create_user(conn, "Bob Builder")
        user_id = existing_user["id"]
    
    # Create a session
    session = service.create_session(title="Construction", host_display_name="Dr. Host")
    
    # Join with existing user's display name
    result = service.join_session(code=session.code, display_name="Bob Builder")
    
    assert isinstance(result, SessionSummary)
    
    # Verify the same user was reused
    with psycopg.connect(dsn, autocommit=True) as conn:
        participant = get_participant(conn, session_id=result.id, user_id=user_id)
        assert participant is not None
        assert participant["user_id"] == user_id


def test_join_session_is_idempotent() -> None:
    """Test joining same session twice with same user succeeds both times."""
    
    service = SessionService(connection_provider=_connection_provider())
    
    # Create a session
    session = service.create_session(title="Math", host_display_name="Prof. Numbers")
    
    # Join once
    result1 = service.join_session(code=session.code, display_name="Alice")
    
    # Join again with same display name
    result2 = service.join_session(code=session.code, display_name="Alice")
    
    # Both should succeed
    assert result1.id == result2.id
    assert result1.code == result2.code
    assert result1.title == result2.title


def test_join_draft_session_succeeds() -> None:
    """Test joining a draft session (default status) succeeds."""
    
    service = SessionService(connection_provider=_connection_provider())
    
    # Create session (default status is 'draft')
    session = service.create_session(title="Draft Session", host_display_name="Dr. Draft")
    
    # Join the draft session
    result = service.join_session(code=session.code, display_name="Participant")
    
    assert isinstance(result, SessionSummary)
    assert result.status == "draft"


def test_join_active_session_succeeds() -> None:
    """Test joining an active session succeeds."""
    
    dsn = get_psycopg_dsn()
    service = SessionService(connection_provider=_connection_provider())
    
    # Create session
    session = service.create_session(title="Active Session", host_display_name="Dr. Active")
    
    # Update status to 'active' via direct SQL
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET status = %s WHERE id = %s",
                ("active", session.id),
            )
    
    # Join the active session
    result = service.join_session(code=session.code, display_name="Participant")
    
    assert isinstance(result, SessionSummary)
    assert result.status == "active"


def test_join_ended_session_raises_error() -> None:
    """Test joining an ended session raises SessionNotJoinableError."""
    
    dsn = get_psycopg_dsn()
    service = SessionService(connection_provider=_connection_provider())
    
    # Create session
    session = service.create_session(title="Ended Session", host_display_name="Dr. Ended")
    
    # Update status to 'ended' via direct SQL
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET status = %s WHERE id = %s",
                ("ended", session.id),
            )
    
    # Attempt to join ended session
    with pytest.raises(SessionNotJoinableError) as exc_info:
        service.join_session(code=session.code, display_name="Too Late")
    
    assert "Session has ended and is no longer joinable" in str(exc_info.value)


def test_join_with_invalid_code_raises_error() -> None:
    """Test joining with non-existent code raises SessionNotFoundError."""
    
    service = SessionService(connection_provider=_connection_provider())
    
    # Attempt to join with invalid code
    with pytest.raises(SessionNotFoundError) as exc_info:
        service.join_session(code="INVALID", display_name="Lost User")
    
    assert "Session not found" in str(exc_info.value)


def test_join_with_whitespace_display_name_raises_error() -> None:
    """Test joining with whitespace-only display name raises error."""
    
    service = SessionService(connection_provider=_connection_provider())
    
    # Create session
    session = service.create_session(title="Test", host_display_name="Dr. Test")
    
    # Attempt to join with whitespace-only display name
    with pytest.raises(InvalidHostDisplayNameError) as exc_info:
        service.join_session(code=session.code, display_name="   ")
    
    assert "Display name is required" in str(exc_info.value)


def test_join_as_host_maintains_host_role() -> None:
    """Test host joining their own session maintains host role (not downgraded)."""
    
    dsn = get_psycopg_dsn()
    service = SessionService(connection_provider=_connection_provider())
    
    # Create session with specific host name
    session = service.create_session(title="My Session", host_display_name="Dr. Host")
    
    # Host joins their own session
    result = service.join_session(code=session.code, display_name="Dr. Host")
    
    assert isinstance(result, SessionSummary)
    assert result.host.display_name == "Dr. Host"
    
    # Verify role in database is still 'host'
    with psycopg.connect(dsn, autocommit=True) as conn:
        participant = get_participant(conn, session_id=result.id, user_id=result.host.id)
        assert participant is not None
        assert participant["role"] == "host"


def test_join_as_non_host_gets_participant_role() -> None:
    """Test non-host joining session gets participant role."""
    
    dsn = get_psycopg_dsn()
    service = SessionService(connection_provider=_connection_provider())
    
    # Create session
    session = service.create_session(title="Class", host_display_name="Professor")
    
    # Non-host joins session
    result = service.join_session(code=session.code, display_name="Student")
    
    assert isinstance(result, SessionSummary)
    assert result.host.display_name == "Professor"
    
    # Verify participant role in database
    with psycopg.connect(dsn, autocommit=True) as conn:
        # Find the student user
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE display_name = %s",
                ("Student",),
            )
            student = cur.fetchone()
            assert student is not None
            student_id = student[0]
        
        participant = get_participant(conn, session_id=result.id, user_id=student_id)
        assert participant is not None
        assert participant["role"] == "participant"


def test_join_session_returns_complete_summary() -> None:
    """Test join_session returns SessionSummary with all required fields."""
    
    service = SessionService(connection_provider=_connection_provider())
    
    # Create and join session
    session = service.create_session(title="Complete Test", host_display_name="Dr. Complete")
    result = service.join_session(code=session.code, display_name="Joiner")
    
    # Verify all fields are present and correct types
    assert isinstance(result, SessionSummary)
    assert isinstance(result.id, int)
    assert isinstance(result.code, str)
    assert len(result.code) == 6
    assert result.title == "Complete Test"
    assert result.status in ("draft", "active", "ended")
    assert result.host.display_name == "Dr. Complete"
    assert result.created_at is not None

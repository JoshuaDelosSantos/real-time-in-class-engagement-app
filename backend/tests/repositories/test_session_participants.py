"""Tests for session_participants repository functions."""

from __future__ import annotations

import pytest  # type: ignore
import psycopg  # type: ignore

from app.repositories import (
    add_participant,
    create_user,
    get_participant,
    insert_session,
    list_session_participants,
)


def test_add_participant_inserts_and_returns_record(db_connection) -> None:
    """Test basic participant insertion returns complete record."""

    user = create_user(db_connection, "Alice")
    session = insert_session(
        db_connection,
        host_user_id=user["id"],
        title="Test Session",
        code="ABC123",
    )

    participant = add_participant(
        db_connection,
        session_id=session["id"],
        user_id=user["id"],
        role="participant",
    )

    assert participant["id"] is not None
    assert participant["session_id"] == session["id"]
    assert participant["user_id"] == user["id"]
    assert participant["role"] == "participant"
    assert participant["joined_at"] is not None


def test_add_participant_idempotent_on_conflict_updates_role(db_connection) -> None:
    """Test ON CONFLICT DO UPDATE behavior maintains idempotency."""

    user = create_user(db_connection, "Bob")
    session = insert_session(
        db_connection,
        host_user_id=user["id"],
        title="Test Session",
        code="XYZ789",
    )

    # First insert: participant role
    first_insert = add_participant(
        db_connection,
        session_id=session["id"],
        user_id=user["id"],
        role="participant",
    )
    first_id = first_insert["id"]
    first_joined_at = first_insert["joined_at"]

    # Second insert: same user, same session, different role
    second_insert = add_participant(
        db_connection,
        session_id=session["id"],
        user_id=user["id"],
        role="host",
    )

    # Verify: same ID (not a new row), role updated, joined_at preserved
    assert second_insert["id"] == first_id
    assert second_insert["role"] == "host"
    assert second_insert["joined_at"] == first_joined_at


def test_add_participant_enforces_session_foreign_key(db_connection) -> None:
    """Test foreign key constraint for invalid session_id."""

    user = create_user(db_connection, "Charlie")

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        add_participant(
            db_connection,
            session_id=99999,  # Non-existent session
            user_id=user["id"],
            role="participant",
        )


def test_add_participant_enforces_user_foreign_key(db_connection) -> None:
    """Test foreign key constraint for invalid user_id."""

    host = create_user(db_connection, "Host")
    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Session",
        code="CODE1",
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        add_participant(
            db_connection,
            session_id=session["id"],
            user_id=99999,  # Non-existent user
            role="participant",
        )


def test_add_participant_accepts_valid_roles(db_connection) -> None:
    """Test that both 'host' and 'participant' roles are accepted."""

    host = create_user(db_connection, "Host User")
    participant_user = create_user(db_connection, "Participant User")
    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Role Test",
        code="ROLES",
    )

    # Add host role
    host_participant = add_participant(
        db_connection,
        session_id=session["id"],
        user_id=host["id"],
        role="host",
    )
    assert host_participant["role"] == "host"

    # Add participant role
    regular_participant = add_participant(
        db_connection,
        session_id=session["id"],
        user_id=participant_user["id"],
        role="participant",
    )
    assert regular_participant["role"] == "participant"


def test_get_participant_returns_record_when_exists(db_connection) -> None:
    """Test retrieving an existing participant record."""

    user = create_user(db_connection, "Diana")
    session = insert_session(
        db_connection,
        host_user_id=user["id"],
        title="Retrieval Test",
        code="GET123",
    )

    # Add participant
    added = add_participant(
        db_connection,
        session_id=session["id"],
        user_id=user["id"],
        role="host",
    )

    # Retrieve participant
    retrieved = get_participant(
        db_connection,
        session_id=session["id"],
        user_id=user["id"],
    )

    assert retrieved is not None
    assert retrieved["id"] == added["id"]
    assert retrieved["session_id"] == session["id"]
    assert retrieved["user_id"] == user["id"]
    assert retrieved["role"] == "host"
    assert retrieved["joined_at"] == added["joined_at"]


def test_get_participant_returns_none_when_not_exists(db_connection) -> None:
    """Test that get_participant returns None for non-existent records."""

    user = create_user(db_connection, "Eve")
    session = insert_session(
        db_connection,
        host_user_id=user["id"],
        title="Non-existent Test",
        code="NONE1",
    )

    # Don't add participant, just try to retrieve
    result = get_participant(
        db_connection,
        session_id=session["id"],
        user_id=user["id"],
    )

    assert result is None


def test_get_participant_returns_none_for_wrong_session(db_connection) -> None:
    """Test that get_participant returns None when querying wrong session."""

    host = create_user(db_connection, "Host")
    user = create_user(db_connection, "Participant")

    session1 = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Session 1",
        code="S1",
    )
    session2 = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Session 2",
        code="S2",
    )

    # Add participant to session1
    add_participant(
        db_connection,
        session_id=session1["id"],
        user_id=user["id"],
        role="participant",
    )

    # Try to retrieve from session2
    result = get_participant(
        db_connection,
        session_id=session2["id"],
        user_id=user["id"],
    )

    assert result is None


# List Session Participants Tests


def test_list_session_participants_returns_empty_for_no_participants(db_connection) -> None:
    """Test listing participants returns empty list when none exist."""

    host = create_user(db_connection, "Lonely Host")
    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Empty Session",
        code="EMPTY1",
    )

    # Don't add any participants
    result = list_session_participants(db_connection, session["id"])

    assert result == []


def test_list_session_participants_returns_all_participants(db_connection) -> None:
    """Test listing participants returns all participant records with user data."""

    host = create_user(db_connection, "Dr. Host")
    participant1 = create_user(db_connection, "Alice")
    participant2 = create_user(db_connection, "Bob")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Popular Session",
        code="POP123",
    )

    # Add host as participant
    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=host["id"],
        role="host",
    )

    # Add participants
    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=participant1["id"],
        role="participant",
    )
    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=participant2["id"],
        role="participant",
    )

    result = list_session_participants(db_connection, session["id"])

    assert len(result) == 3
    # Verify all records have required fields
    for record in result:
        assert "user_id" in record
        assert "display_name" in record
        assert "role" in record
        assert "joined_at" in record


def test_list_session_participants_orders_host_first(db_connection) -> None:
    """Test participants are ordered with host first, then by join time."""

    host = create_user(db_connection, "Dr. Host")
    participant1 = create_user(db_connection, "Early Bird")
    participant2 = create_user(db_connection, "Late Joiner")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Ordered Session",
        code="ORDER1",
    )

    # Add participants in specific order
    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=participant1["id"],
        role="participant",
    )
    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=participant2["id"],
        role="participant",
    )
    # Add host last to verify ordering isn't by insert time
    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=host["id"],
        role="host",
    )

    result = list_session_participants(db_connection, session["id"])

    # Host should be first (role DESC)
    assert result[0]["role"] == "host"
    assert result[0]["display_name"] == "Dr. Host"

    # Participants should follow, ordered by joined_at ASC
    assert result[1]["display_name"] == "Early Bird"
    assert result[2]["display_name"] == "Late Joiner"


def test_list_session_participants_includes_user_details(db_connection) -> None:
    """Test participant records include joined user display names."""

    host = create_user(db_connection, "Prof. Carter")
    participant = create_user(db_connection, "Student Alice")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Test Session",
        code="TEST99",
    )

    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=host["id"],
        role="host",
    )
    add_participant(
        db_connection,
        session_id=session["id"],
        user_id=participant["id"],
        role="participant",
    )

    result = list_session_participants(db_connection, session["id"])

    # Verify user data is included
    assert any(r["display_name"] == "Prof. Carter" for r in result)
    assert any(r["display_name"] == "Student Alice" for r in result)
    
    # Verify user_id matches
    host_record = [r for r in result if r["role"] == "host"][0]
    assert host_record["user_id"] == host["id"]

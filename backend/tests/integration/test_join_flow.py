"""Integration tests for join session flow.

These tests verify end-to-end behavior by making API calls and verifying
database state directly using psycopg.
"""

from __future__ import annotations

import os

import psycopg  # type: ignore
import pytest  # type: ignore
from fastapi.testclient import TestClient  # type: ignore
from psycopg.rows import dict_row  # type: ignore

from app.main import app
from app.settings import get_psycopg_dsn

client = TestClient(app)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:  # pragma: no cover - enforced during test runtime
    pytest.skip("DATABASE_URL must be configured to run integration tests", allow_module_level=True)


def test_join_flow_end_to_end() -> None:
    """Test complete join flow: create session via API → join via API → verify in DB."""
    dsn = get_psycopg_dsn()

    # Step 1: Create session via API
    create_response = client.post(
        "/sessions",
        json={"title": "Physics 301", "host_display_name": "Dr. Einstein"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]
    session_id = session["id"]

    # Step 2: Join session as participant via API
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Student Newton"},
    )
    assert join_response.status_code == 200
    join_body = join_response.json()
    assert join_body["code"] == code
    assert join_body["title"] == "Physics 301"

    # Step 3: Verify participant record exists in database
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT sp.session_id, sp.user_id, sp.role, u.display_name
                FROM session_participants sp
                JOIN users u ON sp.user_id = u.id
                WHERE sp.session_id = %s AND u.display_name = %s
                """,
                (session_id, "Student Newton"),
            )
            participant = cur.fetchone()

    # Assertions on database record
    assert participant is not None
    assert participant["session_id"] == session_id
    assert participant["role"] == "participant"
    assert participant["display_name"] == "Student Newton"


def test_multiple_participants_join() -> None:
    """Test multiple participants can join the same session and all appear in DB."""
    dsn = get_psycopg_dsn()

    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Computer Science 101", "host_display_name": "Prof. Turing"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]
    session_id = session["id"]

    # Join as three different participants
    participants = ["Alice", "Bob", "Charlie"]
    for name in participants:
        join_response = client.post(
            f"/sessions/{code}/join",
            json={"display_name": name},
        )
        assert join_response.status_code == 200

    # Verify all three participants exist in database
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT u.display_name, sp.role
                FROM session_participants sp
                JOIN users u ON sp.user_id = u.id
                WHERE sp.session_id = %s AND sp.role = 'participant'
                ORDER BY u.display_name
                """,
                (session_id,),
            )
            db_participants = cur.fetchall()

    # Assertions
    assert len(db_participants) == 3
    assert db_participants[0]["display_name"] == "Alice"
    assert db_participants[1]["display_name"] == "Bob"
    assert db_participants[2]["display_name"] == "Charlie"
    for p in db_participants:
        assert p["role"] == "participant"


def test_host_role_protection_via_api() -> None:
    """Test that host joining their own session maintains host role in DB."""
    dsn = get_psycopg_dsn()

    # Create session as host
    create_response = client.post(
        "/sessions",
        json={"title": "Biology 201", "host_display_name": "Dr. Darwin"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]
    session_id = session["id"]
    host_user_id = session["host"]["id"]

    # Host joins their own session (should maintain host role)
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Dr. Darwin"},
    )
    assert join_response.status_code == 200

    # Verify host role is preserved in database
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT sp.role, sp.user_id
                FROM session_participants sp
                WHERE sp.session_id = %s AND sp.user_id = %s
                """,
                (session_id, host_user_id),
            )
            participant = cur.fetchone()

    # Assertions
    assert participant is not None
    assert participant["role"] == "host"
    assert participant["user_id"] == host_user_id


def test_idempotent_join_via_api() -> None:
    """Test that joining the same session twice is idempotent (no duplicates in DB)."""
    dsn = get_psycopg_dsn()

    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Chemistry 101", "host_display_name": "Prof. Curie"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]
    session_id = session["id"]

    # Join session as same participant twice
    for _ in range(2):
        join_response = client.post(
            f"/sessions/{code}/join",
            json={"display_name": "Repeat Student"},
        )
        assert join_response.status_code == 200

    # Verify only one participant record exists
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT COUNT(*) as count
                FROM session_participants sp
                JOIN users u ON sp.user_id = u.id
                WHERE sp.session_id = %s AND u.display_name = %s
                """,
                (session_id, "Repeat Student"),
            )
            result = cur.fetchone()

    # Assertion
    assert result is not None
    assert result["count"] == 1

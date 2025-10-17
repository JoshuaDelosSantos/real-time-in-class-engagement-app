from __future__ import annotations

import os

import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore

from app.main import app

client = TestClient(app)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:  # pragma: no cover - enforced during test runtime
    pytest.skip("DATABASE_URL must be configured to run integration tests", allow_module_level=True)


def test_create_session_returns_summary() -> None:
    response = client.post(
        "/sessions",
        json={"title": "Literature", "host_display_name": "Prof. Bloom"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Literature"
    assert body["host"]["display_name"] == "Prof. Bloom"
    assert len(body["code"]) == 6


def test_create_session_enforces_host_limit() -> None:
    for index in range(3):
        res = client.post(
            "/sessions",
            json={"title": f"Session {index}", "host_display_name": "Prof. Limit"},
        )
        assert res.status_code == 201

    final = client.post(
        "/sessions",
        json={"title": "Overflow", "host_display_name": "Prof. Limit"},
    )
    assert final.status_code == 409


def test_create_session_requires_display_name() -> None:
    response = client.post(
        "/sessions",
        json={"title": "Nameless", "host_display_name": ""},
    )
    assert response.status_code == 422


def test_list_sessions_returns_recent_first() -> None:
    # Create two sessions
    response1 = client.post(
        "/sessions",
        json={"title": "First Session", "host_display_name": "Prof. Alpha"},
    )
    assert response1.status_code == 201
    session1 = response1.json()

    response2 = client.post(
        "/sessions",
        json={"title": "Second Session", "host_display_name": "Prof. Beta"},
    )
    assert response2.status_code == 201
    session2 = response2.json()

    # Fetch sessions
    response = client.get("/sessions")
    assert response.status_code == 200
    body = response.json()

    assert isinstance(body, list)
    assert len(body) >= 2
    
    # Verify most recent appears first
    ids = [s["id"] for s in body]
    assert ids.index(session2["id"]) < ids.index(session1["id"])


def test_list_sessions_respects_limit() -> None:
    # Create multiple sessions
    for i in range(5):
        client.post(
            "/sessions",
            json={"title": f"Session {i}", "host_display_name": f"Host {i}"},
        )

    response = client.get("/sessions?limit=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_list_sessions_returns_empty_when_none_available() -> None:
    response = client.get("/sessions")
    assert response.status_code == 200
    body = response.json()
    assert body == []


def test_join_session_returns_summary() -> None:
    """Test successful join returns session summary with participant info."""
    # Create session first
    create_response = client.post(
        "/sessions",
        json={"title": "Philosophy 101", "host_display_name": "Prof. Socrates"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]

    # Join session as participant
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Student Alice"},
    )
    assert join_response.status_code == 200
    body = join_response.json()

    # Verify response structure
    assert body["code"] == code
    assert body["title"] == "Philosophy 101"
    assert body["status"] == "draft"
    assert body["host"]["display_name"] == "Prof. Socrates"
    assert "id" in body
    assert "created_at" in body


def test_join_session_invalid_code_returns_404() -> None:
    """Test joining with non-existent session code returns 404."""
    response = client.post(
        "/sessions/INVALID/join",
        json={"display_name": "Student Bob"},
    )
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "not found" in body["detail"].lower()


def test_join_session_ended_session_returns_409() -> None:
    """Test joining an ended session returns 409 conflict."""
    import psycopg  # type: ignore
    from app.settings import get_psycopg_dsn

    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Finished Course", "host_display_name": "Prof. Done"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]

    # Mark session as ended via direct SQL
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET status = 'ended' WHERE code = %s",
                (code,),
            )

    # Attempt to join ended session
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Late Student"},
    )
    assert join_response.status_code == 409
    body = join_response.json()
    assert "detail" in body
    assert "no longer joinable" in body["detail"].lower()


def test_join_session_whitespace_display_name_returns_400() -> None:
    """Test joining with whitespace-only display name returns 400."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Math 201", "host_display_name": "Prof. Numbers"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]

    # Attempt join with whitespace-only display name
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "   "},
    )
    assert join_response.status_code == 400
    body = join_response.json()
    assert "detail" in body
    assert "display name" in body["detail"].lower()


def test_join_session_empty_display_name_returns_422() -> None:
    """Test joining with empty display name returns 422 validation error."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Chemistry", "host_display_name": "Prof. Beaker"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]

    # Attempt join with empty display name
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": ""},
    )
    assert join_response.status_code == 422


def test_join_session_response_validation() -> None:
    """Test that join response matches SessionSummary schema exactly."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Biology", "host_display_name": "Prof. Darwin"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]

    # Join session
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Curious Student"},
    )
    assert join_response.status_code == 200
    body = join_response.json()

    # Validate required fields exist
    required_fields = {"id", "code", "title", "status", "host", "created_at"}
    assert set(body.keys()) == required_fields

    # Validate host structure
    assert "id" in body["host"]
    assert "display_name" in body["host"]
    assert body["host"]["display_name"] == "Prof. Darwin"

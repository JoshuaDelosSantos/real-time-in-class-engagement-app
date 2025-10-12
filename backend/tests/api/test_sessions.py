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

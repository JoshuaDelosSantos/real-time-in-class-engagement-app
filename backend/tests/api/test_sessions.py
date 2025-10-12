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
    assert response.status_code == 400
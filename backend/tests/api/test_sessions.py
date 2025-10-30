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


# Get Session Details Tests


def test_get_session_returns_complete_details() -> None:
    """Test GET /sessions/{code} returns complete session details."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Mathematics", "host_display_name": "Prof. Euler"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    code = created["code"]

    # Retrieve session by code
    response = client.get(f"/sessions/{code}")
    assert response.status_code == 200
    body = response.json()

    # Validate response matches created session
    assert body["id"] == created["id"]
    assert body["code"] == code
    assert body["title"] == "Mathematics"
    assert body["status"] == "draft"
    assert body["host"]["display_name"] == "Prof. Euler"
    assert body["created_at"] == created["created_at"]


def test_get_session_returns_404_for_invalid_code() -> None:
    """Test GET /sessions/{code} returns 404 for non-existent session."""
    response = client.get("/sessions/INVALID")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "not found" in body["detail"].lower()


def test_get_session_response_schema() -> None:
    """Test GET /sessions/{code} response matches SessionSummary schema."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Chemistry", "host_display_name": "Prof. Curie"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Retrieve session
    response = client.get(f"/sessions/{code}")
    assert response.status_code == 200
    body = response.json()

    # Validate schema
    required_fields = {"id", "code", "title", "status", "host", "created_at"}
    assert set(body.keys()) == required_fields
    
    # Validate host structure
    assert "id" in body["host"]
    assert "display_name" in body["host"]
    assert isinstance(body["host"]["id"], int)
    assert isinstance(body["host"]["display_name"], str)


# Get Session Participants Tests


def test_get_participants_returns_empty_for_no_participants() -> None:
    """Test GET /sessions/{code}/participants returns empty array when no participants."""
    # Create session without joining
    create_response = client.post(
        "/sessions",
        json={"title": "Empty Session", "host_display_name": "Dr. Solo"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Retrieve participants
    response = client.get(f"/sessions/{code}/participants")
    assert response.status_code == 200
    body = response.json()
    
    # Host is added as participant during session creation
    assert len(body) == 1
    assert body[0]["role"] == "host"


def test_get_participants_returns_all_participants() -> None:
    """Test GET /sessions/{code}/participants returns complete participant list."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Popular Class", "host_display_name": "Dr. Popular"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Join as participants
    client.post(f"/sessions/{code}/join", json={"display_name": "Alice"})
    client.post(f"/sessions/{code}/join", json={"display_name": "Bob"})

    # Retrieve participants
    response = client.get(f"/sessions/{code}/participants")
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 3  # Host + 2 participants
    
    # Verify host is first
    assert body[0]["role"] == "host"
    assert body[0]["user"]["display_name"] == "Dr. Popular"
    
    # Verify participants present
    participant_names = [p["user"]["display_name"] for p in body[1:]]
    assert "Alice" in participant_names
    assert "Bob" in participant_names


def test_get_participants_returns_404_for_invalid_code() -> None:
    """Test GET /sessions/{code}/participants returns 404 for non-existent session."""
    response = client.get("/sessions/INVALID/participants")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "not found" in body["detail"].lower()


def test_get_participants_response_schema() -> None:
    """Test GET /sessions/{code}/participants response matches schema."""
    # Create and join session
    create_response = client.post(
        "/sessions",
        json={"title": "Test Session", "host_display_name": "Dr. Test"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]
    
    client.post(f"/sessions/{code}/join", json={"display_name": "Student"})

    # Retrieve participants
    response = client.get(f"/sessions/{code}/participants")
    assert response.status_code == 200
    body = response.json()

    # Validate schema
    assert isinstance(body, list)
    for participant in body:
        assert "user" in participant
        assert "role" in participant
        assert "joined_at" in participant
        
        # Validate user structure
        assert "id" in participant["user"]
        assert "display_name" in participant["user"]
        assert isinstance(participant["user"]["id"], int)
        assert isinstance(participant["user"]["display_name"], str)


# Get Session Questions Tests


def test_get_questions_returns_empty_for_no_questions() -> None:
    """Test GET /sessions/{code}/questions returns empty array when no questions."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "No Questions", "host_display_name": "Dr. Empty"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Retrieve questions
    response = client.get(f"/sessions/{code}/questions")
    assert response.status_code == 200
    body = response.json()
    
    assert body == []


def test_get_questions_returns_all_questions() -> None:
    """Test GET /sessions/{code}/questions returns complete question list."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Q&A Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    session = create_response.json()
    code = session["code"]

    # Add questions directly to database
    from app.repositories import create_user
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        author = create_user(conn, "Alice")
        
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sessions WHERE code = %s", (code,))
            session_id = cur.fetchone()[0]
        
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO questions (session_id, author_user_id, body, status, likes)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, author["id"], "Great question!", "pending", 5),
            )

    # Retrieve questions
    response = client.get(f"/sessions/{code}/questions")
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert body[0]["body"] == "Great question!"
    assert body[0]["status"] == "pending"
    assert body[0]["likes"] == 5
    assert body[0]["author"]["display_name"] == "Alice"


def test_get_questions_handles_null_author() -> None:
    """Test GET /sessions/{code}/questions handles anonymous questions."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Anonymous Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Add anonymous question
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sessions WHERE code = %s", (code,))
            session_id = cur.fetchone()[0]
        
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO questions (session_id, author_user_id, body, status)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, None, "Anonymous question", "pending"),
            )

    # Retrieve questions
    response = client.get(f"/sessions/{code}/questions")
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert body[0]["body"] == "Anonymous question"
    assert body[0]["author"] is None


def test_get_questions_filters_by_status() -> None:
    """Test GET /sessions/{code}/questions?status= filters correctly."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Filtered Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Add questions with different statuses
    from app.repositories import create_user
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        author = create_user(conn, "Student")
        
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sessions WHERE code = %s", (code,))
            session_id = cur.fetchone()[0]
        
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO questions (session_id, author_user_id, body, status)
                VALUES 
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s)
                """,
                (
                    session_id, author["id"], "Pending 1", "pending",
                    session_id, author["id"], "Answered", "answered",
                    session_id, author["id"], "Pending 2", "pending",
                ),
            )

    # Filter for pending
    response = client.get(f"/sessions/{code}/questions?status=pending")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert all(q["status"] == "pending" for q in body)

    # Filter for answered
    response = client.get(f"/sessions/{code}/questions?status=answered")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "answered"

    # No filter returns all
    response = client.get(f"/sessions/{code}/questions")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3


def test_get_questions_returns_404_for_invalid_code() -> None:
    """Test GET /sessions/{code}/questions returns 404 for non-existent session."""
    response = client.get("/sessions/INVALID/questions")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "not found" in body["detail"].lower()


def test_get_questions_response_schema() -> None:
    """Test GET /sessions/{code}/questions response matches schema."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Schema Test", "host_display_name": "Dr. Test"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Add question
    from app.repositories import create_user
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        author = create_user(conn, "Author")
        
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sessions WHERE code = %s", (code,))
            session_id = cur.fetchone()[0]
        
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO questions (session_id, author_user_id, body, status, likes)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, author["id"], "Test question", "pending", 10),
            )

    # Retrieve questions
    response = client.get(f"/sessions/{code}/questions")
    assert response.status_code == 200
    body = response.json()

    # Validate schema
    assert isinstance(body, list)
    assert len(body) == 1
    
    question = body[0]
    required_fields = {"id", "session_id", "body", "status", "likes", "author", "created_at"}
    assert set(question.keys()) == required_fields
    
    # Validate types
    assert isinstance(question["id"], int)
    assert isinstance(question["session_id"], int)
    assert isinstance(question["body"], str)
    assert question["status"] in ("pending", "answered")
    assert isinstance(question["likes"], int)
    assert isinstance(question["created_at"], str)
    
    # Validate author structure
    assert question["author"] is not None
    assert "id" in question["author"]
    assert "display_name" in question["author"]
    assert isinstance(question["author"]["id"], int)
    assert isinstance(question["author"]["display_name"], str)


# Post Question Tests


def test_post_question_success_201() -> None:
    """Test POST /sessions/{code}/questions creates question and returns 201."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Test Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Join as participant
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Alice"},
    )
    assert join_response.status_code == 200
    
    # Get user ID from database
    from app.repositories import get_user_by_display_name
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        user = get_user_by_display_name(conn, "Alice")
        assert user is not None
        user_id = user["id"]

    # Submit question
    response = client.post(
        f"/sessions/{code}/questions",
        json={"body": "What is polymorphism?"},
        headers={"X-User-Id": str(user_id)},
    )
    assert response.status_code == 201
    body = response.json()
    
    # Validate response
    assert body["body"] == "What is polymorphism?"
    assert body["status"] == "pending"
    assert body["likes"] == 0
    assert body["author"]["display_name"] == "Alice"
    assert "id" in body
    assert "session_id" in body
    assert "created_at" in body


def test_post_question_missing_user_id_header_422() -> None:
    """Test POST /sessions/{code}/questions returns 422 when X-User-Id header is missing."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Test Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Attempt to submit question without X-User-Id header
    response = client.post(
        f"/sessions/{code}/questions",
        json={"body": "Question without user ID?"},
    )
    assert response.status_code == 422


def test_post_question_session_not_found_404() -> None:
    """Test POST /sessions/{code}/questions returns 404 for non-existent session."""
    response = client.post(
        "/sessions/INVALID/questions",
        json={"body": "Question for non-existent session"},
        headers={"X-User-Id": "999"},
    )
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "not found" in body["detail"].lower()


def test_post_question_not_participant_403() -> None:
    """Test POST /sessions/{code}/questions returns 403 when user is not a participant."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Exclusive Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Create a user who doesn't join
    from app.repositories import create_user
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        outsider = create_user(conn, "Outsider")

    # Attempt to submit question as non-participant
    response = client.post(
        f"/sessions/{code}/questions",
        json={"body": "Can I ask without joining?"},
        headers={"X-User-Id": str(outsider["id"])},
    )
    assert response.status_code == 403
    body = response.json()
    assert "detail" in body
    assert "participant" in body["detail"].lower()


def test_post_question_limit_exceeded_409() -> None:
    """Test POST /sessions/{code}/questions returns 409 when user exceeds 3 pending question limit."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Busy Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Join as participant
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Curious Student"},
    )
    assert join_response.status_code == 200

    # Get user ID
    from app.repositories import get_user_by_display_name
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        user = get_user_by_display_name(conn, "Curious Student")
        assert user is not None
        user_id = user["id"]

    # Submit 3 questions (should all succeed)
    for i in range(3):
        response = client.post(
            f"/sessions/{code}/questions",
            json={"body": f"Question {i + 1}?"},
            headers={"X-User-Id": str(user_id)},
        )
        assert response.status_code == 201

    # Attempt 4th question (should fail)
    response = client.post(
        f"/sessions/{code}/questions",
        json={"body": "Question 4 exceeds limit?"},
        headers={"X-User-Id": str(user_id)},
    )
    assert response.status_code == 409
    body = response.json()
    assert "detail" in body
    assert "3 pending questions" in body["detail"].lower()


def test_post_question_body_validation_422() -> None:
    """Test POST /sessions/{code}/questions returns 422 for invalid body content."""
    # Create session
    create_response = client.post(
        "/sessions",
        json={"title": "Validation Session", "host_display_name": "Dr. Host"},
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    # Join as participant
    join_response = client.post(
        f"/sessions/{code}/join",
        json={"display_name": "Validator"},
    )
    assert join_response.status_code == 200

    # Get user ID
    from app.repositories import get_user_by_display_name
    from app.settings import get_psycopg_dsn
    import psycopg
    
    dsn = get_psycopg_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        user = get_user_by_display_name(conn, "Validator")
        assert user is not None
        user_id = user["id"]

    # Test empty body (Pydantic validation should catch this at 422 level before service)
    response = client.post(
        f"/sessions/{code}/questions",
        json={"body": ""},
        headers={"X-User-Id": str(user_id)},
    )
    assert response.status_code == 422

    # Test body exceeds max length (280 chars)
    long_body = "x" * 281
    response = client.post(
        f"/sessions/{code}/questions",
        json={"body": long_body},
        headers={"X-User-Id": str(user_id)},
    )
    assert response.status_code == 422

    # Test whitespace-only body (service-level validation via ValueError → 422)
    response = client.post(
        f"/sessions/{code}/questions",
        json={"body": "   "},
        headers={"X-User-Id": str(user_id)},
    )
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert "empty" in body["detail"].lower()


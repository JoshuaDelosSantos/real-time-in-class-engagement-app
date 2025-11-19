"""Tests for questions repository functions."""

from __future__ import annotations

import pytest  # type: ignore
import psycopg  # type: ignore

from app.repositories import (
    create_user,
    insert_session,
    list_session_questions,
    create_question,
    count_user_pending_questions,
)


def test_list_session_questions_returns_empty_for_no_questions(db_connection) -> None:
    """Test listing questions returns empty list when none exist."""

    host = create_user(db_connection, "Dr. Empty")
    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="No Questions Session",
        code="EMPTY1",
    )

    result = list_session_questions(db_connection, session["id"])

    assert result == []


def test_list_session_questions_returns_all_questions(db_connection) -> None:
    """Test listing questions returns all question records with author data."""

    host = create_user(db_connection, "Dr. Host")
    author1 = create_user(db_connection, "Alice")
    author2 = create_user(db_connection, "Bob")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Active Session",
        code="ACTIVE",
    )

    # Insert questions directly
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status, likes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session["id"], author1["id"], "What is the answer?", "pending", 5),
        )
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status, likes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session["id"], author2["id"], "Can you explain more?", "answered", 3),
        )

    result = list_session_questions(db_connection, session["id"])

    assert len(result) == 2
    # Verify all records have required fields
    for record in result:
        assert "id" in record
        assert "session_id" in record
        assert "body" in record
        assert "status" in record
        assert "likes" in record
        assert "author_user_id" in record
        assert "author_display_name" in record
        assert "created_at" in record


def test_list_session_questions_orders_by_created_desc(db_connection) -> None:
    """Test questions are ordered by creation time (newest first)."""

    host = create_user(db_connection, "Dr. Host")
    author = create_user(db_connection, "Student")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Ordered Session",
        code="ORDER1",
    )

    # Insert questions separately to ensure different timestamps
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status)
            VALUES (%s, %s, %s, %s)
            """,
            (session["id"], author["id"], "First question", "pending"),
        )
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status)
            VALUES (%s, %s, %s, %s)
            """,
            (session["id"], author["id"], "Second question", "pending"),
        )
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status)
            VALUES (%s, %s, %s, %s)
            """,
            (session["id"], author["id"], "Third question", "pending"),
        )

    result = list_session_questions(db_connection, session["id"])

    # Should be ordered by created_at DESC (newest first)
    # Since inserts happened sequentially, third is newest
    assert len(result) == 3
    assert result[0]["body"] == "Third question"
    assert result[1]["body"] == "Second question"
    assert result[2]["body"] == "First question"


def test_list_session_questions_filters_by_status(db_connection) -> None:
    """Test questions can be filtered by status."""

    host = create_user(db_connection, "Dr. Host")
    author = create_user(db_connection, "Student")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Filtered Session",
        code="FILTER",
    )

    # Insert questions with different statuses
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status)
            VALUES 
                (%s, %s, %s, %s),
                (%s, %s, %s, %s),
                (%s, %s, %s, %s)
            """,
            (
                session["id"], author["id"], "Pending question 1", "pending",
                session["id"], author["id"], "Answered question", "answered",
                session["id"], author["id"], "Pending question 2", "pending",
            ),
        )

    # Filter for pending only
    pending_result = list_session_questions(db_connection, session["id"], status_filter="pending")
    assert len(pending_result) == 2
    assert all(q["status"] == "pending" for q in pending_result)

    # Filter for answered only
    answered_result = list_session_questions(db_connection, session["id"], status_filter="answered")
    assert len(answered_result) == 1
    assert answered_result[0]["status"] == "answered"

    # No filter returns all
    all_result = list_session_questions(db_connection, session["id"])
    assert len(all_result) == 3


def test_list_session_questions_handles_null_author(db_connection) -> None:
    """Test questions with NULL author_user_id are handled correctly."""

    host = create_user(db_connection, "Dr. Host")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Anonymous Session",
        code="ANON1",
    )

    # Insert anonymous question (NULL author)
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status)
            VALUES (%s, %s, %s, %s)
            """,
            (session["id"], None, "Anonymous question", "pending"),
        )

    result = list_session_questions(db_connection, session["id"])

    assert len(result) == 1
    assert result[0]["body"] == "Anonymous question"
    assert result[0]["author_user_id"] is None
    assert result[0]["author_display_name"] is None


def test_list_session_questions_includes_author_details(db_connection) -> None:
    """Test question records include author display names from JOIN."""

    host = create_user(db_connection, "Prof. Smith")
    author = create_user(db_connection, "Alice Wonder")

    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Test Session",
        code="TEST99",
    )

    # Insert question
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status, likes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session["id"], author["id"], "Great question!", "pending", 10),
        )

    result = list_session_questions(db_connection, session["id"])

    # Verify author data is included
    assert result[0]["author_user_id"] == author["id"]
    assert result[0]["author_display_name"] == "Alice Wonder"
    assert result[0]["likes"] == 10


def test_create_question_with_author(db_connection) -> None:
    """Test creating a question with an author user_id."""
    
    host = create_user(db_connection, "Prof. Smith")
    author = create_user(db_connection, "Student Alice")
    
    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Test Session",
        code="TEST01",
    )
    
    # Create question with author
    result = create_question(
        db_connection,
        session_id=session["id"],
        author_user_id=author["id"],
        body="What is the meaning of life?",
    )
    
    # Verify all fields are returned
    assert result["id"] is not None
    assert result["session_id"] == session["id"]
    assert result["author_user_id"] == author["id"]
    assert result["body"] == "What is the meaning of life?"
    assert result["status"] == "pending"
    assert result["likes"] == 0
    assert result["created_at"] is not None
    assert result["answered_at"] is None


def test_create_question_anonymous(db_connection) -> None:
    """Test creating a question with NULL author_user_id (anonymous)."""
    
    host = create_user(db_connection, "Prof. Smith")
    
    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Anonymous Session",
        code="ANON01",
    )
    
    # Create anonymous question
    result = create_question(
        db_connection,
        session_id=session["id"],
        author_user_id=None,
        body="Anonymous question here",
    )
    
    # Verify anonymous question created successfully
    assert result["id"] is not None
    assert result["session_id"] == session["id"]
    assert result["author_user_id"] is None
    assert result["body"] == "Anonymous question here"
    assert result["status"] == "pending"
    assert result["likes"] == 0


def test_count_user_pending_questions(db_connection) -> None:
    """Test counting pending questions for a user in a session."""
    
    host = create_user(db_connection, "Prof. Host")
    author = create_user(db_connection, "Student Bob")
    
    session = insert_session(
        db_connection,
        host_user_id=host["id"],
        title="Count Test Session",
        code="COUNT1",
    )
    
    # Initially zero questions
    count = count_user_pending_questions(db_connection, session["id"], author["id"])
    assert count == 0
    
    # Create first pending question
    create_question(
        db_connection,
        session_id=session["id"],
        author_user_id=author["id"],
        body="First question",
    )
    
    count = count_user_pending_questions(db_connection, session["id"], author["id"])
    assert count == 1
    
    # Create second pending question
    create_question(
        db_connection,
        session_id=session["id"],
        author_user_id=author["id"],
        body="Second question",
    )
    
    count = count_user_pending_questions(db_connection, session["id"], author["id"])
    assert count == 2
    
    # Create an answered question (should not be counted)
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status)
            VALUES (%s, %s, %s, 'answered')
            """,
            (session["id"], author["id"], "Answered question"),
        )
    
    # Count should still be 2 (only pending)
    count = count_user_pending_questions(db_connection, session["id"], author["id"])
    assert count == 2
    
    # Create question from different user (should not be counted)
    other_user = create_user(db_connection, "Other Student")
    create_question(
        db_connection,
        session_id=session["id"],
        author_user_id=other_user["id"],
        body="Other user's question",
    )
    
    # Count should still be 2 (only author's pending questions)
    count = count_user_pending_questions(db_connection, session["id"], author["id"])
    assert count == 2

"""Repository helpers for questions."""

from __future__ import annotations

from typing import Optional

import psycopg # type: ignore
from psycopg.rows import dict_row # type: ignore


def list_session_questions(
    conn: psycopg.Connection,
    session_id: int,
    status_filter: Optional[str] = None,
) -> list[dict]:
    """List all questions for a session with author details.
    
    Returns questions ordered by creation time (newest first).
    Author fields may be NULL for anonymous questions.
    """

    with conn.cursor(row_factory=dict_row) as cur:
        query = """
            SELECT 
                q.id,
                q.session_id,
                q.body,
                q.status,
                q.likes,
                q.author_user_id,
                u.display_name AS author_display_name,
                q.created_at
            FROM questions q
            LEFT JOIN users u ON q.author_user_id = u.id
            WHERE q.session_id = %s
        """
        params = [session_id]
        
        if status_filter:
            query += " AND q.status = %s"
            params.append(status_filter)
        
        query += " ORDER BY q.created_at DESC"
        
        cur.execute(query, params)
        return cur.fetchall()


def create_question(
    conn: psycopg.Connection,
    *,
    session_id: int,
    author_user_id: int | None,
    body: str,
) -> dict:
    """Create a new question and return the complete record.
    
    Args:
        conn: Database connection
        session_id: ID of the session this question belongs to
        author_user_id: ID of the user submitting the question (None for anonymous)
        body: Question text content
        
    Returns:
        Complete question record with all fields
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body, status, likes)
            VALUES (%s, %s, %s, 'pending', 0)
            RETURNING id, session_id, author_user_id, body, status, likes, created_at, answered_at
            """,
            (session_id, author_user_id, body),
        )
        return cur.fetchone()


def count_user_pending_questions(
    conn: psycopg.Connection,
    session_id: int,
    user_id: int,
) -> int:
    """Count pending questions for a specific user in a session.
    
    Used to enforce per-user question limits.
    
    Args:
        conn: Database connection
        session_id: ID of the session
        user_id: ID of the user
        
    Returns:
        Number of pending questions for this user in this session
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM questions
            WHERE session_id = %s 
              AND author_user_id = %s 
              AND status = 'pending'
            """,
            (session_id, user_id),
        )
        result = cur.fetchone()
        return result[0] if result else 0

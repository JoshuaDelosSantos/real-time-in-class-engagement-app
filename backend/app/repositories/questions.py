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

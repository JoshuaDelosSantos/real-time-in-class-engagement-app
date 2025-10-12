#!/usr/bin/env python3
"""Seed the database with sample sessions for development and testing.

This script creates three sessions with different hosts to populate the
application with realistic demo data.
"""

from __future__ import annotations

import sys

import psycopg  # type: ignore

from apply_migrations import get_database_url, _normalize_dsn


SAMPLE_SESSIONS = [
    {
        "title": "Introduction to Python",
        "host_display_name": "Shrek",
        "code": "PYTHON",
    },
    {
        "title": "Data Structures & Algorithms",
        "host_display_name": "Donkey",
        "code": "DSA101",
    },
    {
        "title": "Web Development Fundamentals",
        "host_display_name": "Lord Farquaad",
        "code": "WEB101",
    },
]


def create_user(conn: psycopg.Connection, display_name: str) -> dict:
    """Create a user and return their record."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (display_name) VALUES (%s) RETURNING id, display_name",
            (display_name,),
        )
        row = cur.fetchone()
        return {"id": row[0], "display_name": row[1]}


def create_session(
    conn: psycopg.Connection,
    *,
    host_user_id: int,
    title: str,
    code: str,
) -> dict:
    """Create a session and return its record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (host_user_id, title, code, status)
            VALUES (%s, %s, %s, 'draft')
            RETURNING id, title, code
            """,
            (host_user_id, title, code),
        )
        row = cur.fetchone()
        return {"id": row[0], "title": row[1], "code": row[2]}


def add_participant(
    conn: psycopg.Connection,
    *,
    session_id: int,
    user_id: int,
    role: str = "host",
) -> None:
    """Add a participant to a session."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO session_participants (session_id, user_id, role)
            VALUES (%s, %s, %s)
            """,
            (session_id, user_id, role),
        )


def seed_sessions(*, dsn: str | None = None, quiet: bool = False) -> None:
    """Seed the database with sample sessions."""
    
    database_dsn = dsn or get_database_url()
    database_dsn = _normalize_dsn(database_dsn)
    
    if not quiet:
        print(f"Seeding {len(SAMPLE_SESSIONS)} sample sessions...")
    
    with psycopg.connect(database_dsn, autocommit=True) as conn:
        for session_data in SAMPLE_SESSIONS:
            # Create or find host
            host = create_user(conn, session_data["host_display_name"])
            
            # Create session
            session = create_session(
                conn,
                host_user_id=host["id"],
                title=session_data["title"],
                code=session_data["code"],
            )
            
            # Add host as participant
            add_participant(
                conn,
                session_id=session["id"],
                user_id=host["id"],
                role="host",
            )
            
            if not quiet:
                print(f"  ✓ Created session '{session['title']}' (code: {session['code']}) hosted by {host['display_name']}")
    
    if not quiet:
        print("Seeding complete!")


def main() -> None:
    try:
        seed_sessions()
    except Exception as exc:
        print(f"Error seeding sessions: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

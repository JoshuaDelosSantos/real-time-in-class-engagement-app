"""Apply SQL migrations located under backend/migrations.

This lightweight runner executes all `.sql` files in lexical order using a
single psycopg connection derived from the DATABASE_URL environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg # type: ignore

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "backend" / "migrations"


def get_database_url() -> str:
    try:
        return os.environ["DATABASE_URL"]
    except KeyError as exc:  # pragma: no cover - configuration error path
        raise RuntimeError("DATABASE_URL must be set to run migrations") from exc


def load_sql_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        raise RuntimeError(f"Migrations directory missing: {MIGRATIONS_DIR}")
    return sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))


def apply_migration(conn: psycopg.Connection, file_path: Path) -> None:
    with file_path.open("r", encoding="utf-8") as handle:
        statements = handle.read()
    with conn.cursor() as cur:
        cur.execute(statements)


def main() -> None:
    dsn = get_database_url()
    files = load_sql_files()
    if not files:
        print("No migrations to apply.")
        return

    print(f"Applying {len(files)} migration(s)...")
    with psycopg.connect(dsn, autocommit=True) as conn:
        for file_path in files:
            print(f" -> {file_path.name}")
            apply_migration(conn, file_path)

    print("Migrations applied successfully.")


if __name__ == "__main__":
    main()

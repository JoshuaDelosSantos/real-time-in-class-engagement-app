from __future__ import annotations

import os


def get_database_url() -> str:
    """Return the application database URL from the environment."""
    try:
        url = os.environ["DATABASE_URL"]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise RuntimeError("DATABASE_URL environment variable is required") from exc
    return url


def get_psycopg_dsn() -> str:
    """Normalise DATABASE_URL for psycopg connections."""
    url = get_database_url()
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url.split("postgresql+psycopg://", 1)[1]
    return url

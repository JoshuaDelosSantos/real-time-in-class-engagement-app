# Scripts

Utility helpers that streamline development and operations belong here.

Current scripts:

- `apply_migrations.py` — applies all SQL files under `backend/migrations/` using psycopg. It reads `DATABASE_URL`, normalises SQLAlchemy-style DSNs, and runs migrations in lexical order. The Docker Compose stack invokes this script automatically before the API starts.

- `seed_sessions.py` — populates the database with three sample sessions, each with a different host. Useful for development and testing when you need realistic demo data. Run via `docker compose exec swampninjas python /app/scripts/seed_sessions.py`.

Add new scripts alongside documentation describing parameters or environment requirements.

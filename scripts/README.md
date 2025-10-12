# Scripts

Utility helpers that streamline development and operations belong here.

Current scripts:

- `apply_migrations.py` — applies all SQL files under `backend/migrations/` using psycopg. It reads `DATABASE_URL`, normalises SQLAlchemy-style DSNs, and runs migrations in lexical order. The Docker Compose stack invokes this script automatically before the API starts.

Add new scripts alongside documentation describing parameters or environment requirements.

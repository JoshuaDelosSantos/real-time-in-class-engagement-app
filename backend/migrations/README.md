# Database Migrations

SQL files in this directory are executed in lexical order to evolve the database schema. Filenames should use a numeric prefix (e.g. `0001_`, `0002_`) followed by a concise description so newly added migrations append naturally.

## Workflow

1. Add a new `.sql` file describing the schema change.
2. Run `python scripts/apply_migrations.py` (see below) to apply pending migrations locally.
3. Commit both the migration file and any accompanying application changes.

## Apply Script

The repository includes `scripts/apply_migrations.py`, a lightweight runner that executes all SQL files in order. It uses the `DATABASE_URL` environment variable, matching the existing FastAPI configuration.

```bash
python scripts/apply_migrations.py
```

The script is idempotent: each migration should contain `CREATE ... IF NOT EXISTS` or other defensive checks to allow re-runs. When more sophisticated tracking is required, consider introducing a version table or a migration framework such as Alembic.

# App Package

Core application code for the ClassEngage FastAPI service lives here.

- `main.py` exposes the FastAPI application instance and HTTP routes.
- `db.py` houses lightweight helpers for connecting to PostgreSQL.
- `settings.py` centralises environment-dependent configuration such as `DATABASE_URL`.

Modules should avoid heavy framework logic; keep business rules and integrations in clearly named submodules as the project grows.

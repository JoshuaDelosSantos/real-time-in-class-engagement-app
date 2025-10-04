# App Package

Core application code for the ClassEngage FastAPI service lives here.

- `main.py` configures the FastAPI application, middleware, static assets, and router wiring.
- `api/` contains modular FastAPI routers that translate HTTP requests into service calls.
- `services/` encapsulates business workflows and orchestrates repositories.
- `repositories/` performs data-access operations with parameterised queries.
- `schemas/` defines shared Pydantic request/response models.
- `db.py` houses lightweight helpers for connecting to PostgreSQL.
- `settings.py` centralises environment-dependent configuration such as `DATABASE_URL`.

Modules should avoid heavy framework logic; keep business rules and integrations in the appropriate layer so concerns remain separated as the project grows.

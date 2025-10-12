# App Package

Core application code for the ClassEngage FastAPI service lives here.

- `main.py` configures the FastAPI application, middleware, static assets, and router wiring.
- `api/` contains modular FastAPI routers that translate HTTP requests into service calls.
- `services/` encapsulates business workflows and orchestrates repositories.
- `repositories/` performs data-access operations with parameterised queries.
- `schemas/` defines shared Pydantic request/response models.
- `db.py` houses lightweight helpers for connecting to PostgreSQL.
- `settings.py` centralises environment-dependent configuration such as `DATABASE_URL`.

## Example Flow

### Health Check

1. **Router** (`api/routes/health.py`): returns a static heartbeat payload and serves the frontend index page.
2. **Service** (`services/health.py`): provides the heartbeat message consumed by the router.

### Session Creation

1. **Router** (`api/routes/sessions.py`):
   - Handles `POST /sessions` with `SessionCreate`, validating the title and host display name.
   - Translates service exceptions into HTTP 400/409 responses.

2. **Service** (`services/sessions.py`):
   - Looks up or creates the host user, enforces the three-active-session limit, and retries join-code generation on collisions.
   - Coordinates repository calls to persist both the session and the host participant row.
   - Returns a `SessionSummary` response model.

3. **Repositories** (`repositories/users.py`, `repositories/sessions.py`, `repositories/session_participants.py`):
   - Execute parameterised SQL statements against PostgreSQL and return dictionary rows for service consumption.

Modules should avoid heavy framework logic; keep business rules and integrations in the appropriate layer so concerns remain separated as the project grows.
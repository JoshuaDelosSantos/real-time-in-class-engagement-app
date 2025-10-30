# Backend

This directory will house the FastAPI service powering ClassEngage.

- `app/` will contain routers, services, schemas, and core modules.
- `tests/` will collect unit and integration coverage.
- `migrations/` will store database change sets once migration tooling is added.

Refer to the root documentation for setup instructions as they are introduced.

## Session Endpoints

The backend now exposes a complete session detail surface for frontend consumers:

- `POST /sessions` — create sessions and return a summary payload with join code.
- `GET /sessions` — list recent, joinable sessions (draft and active only).
- `POST /sessions/{code}/join` — join a session, creating participant records as needed.
- `GET /sessions/{code}` — retrieve full session details including host summary.
- `GET /sessions/{code}/participants` — fetch participant roster ordered host-first with join timestamps.
- `GET /sessions/{code}/questions` — list session questions with optional status filtering and author information.
- `POST /sessions/{code}/questions` — submit questions to a session (3 pending question limit per user).

## Running Tests
Ensure the Docker stack is running (the API container named `swampninjas` needs access to the Postgres service). Then execute:

```
docker compose exec swampninjas pytest
```

The test suite covers repositories, services, API routes, and integration flows (98 tests as of 2025-10-30). The command above runs the full suite inside the container so database interactions occur against the live Postgres instance.

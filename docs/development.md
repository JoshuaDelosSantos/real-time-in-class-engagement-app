# Local Development Guide

## Prerequisites
- **Docker Desktop** (or Docker Engine) with Compose support.
- **Git** for cloning the repository.
- Optional: Python 3.11+ and `pip` if you want to run backend code outside containers.

## First-time setup
1. Clone the repo:
   ```bash
   git clone https://github.com/JoshuaDelosSantos/real-time-in-class-engagement-app.git
   cd real-time-in-class-engagement-app
   ```
2. Copy the environment template:
   ```bash
   cd infra
   // Insert .env file here
   ```

## Starting the stack
1. Ensure Docker Desktop is running.
2. From `infra/`, build and start services:
   ```bash
   docker compose up -d --build
   ```
   - FastAPI API runs in the `swampninjas` container on http://localhost:8000.
   - PostgreSQL runs in the `db` container on port 5432. Credentials are taken from `.env`.
3. View logs or stop services:
   ```bash
   docker compose logs -f swampninjas
   docker compose down
   ```

## Running tests
- Execute the backend integration tests (API + Postgres):
  ```bash
  docker compose exec swampninjas pytest
  ```
- To wipe the database volume (for a fresh start):
  ```bash
  docker compose down -v
  docker compose up -d --build
  ```

## Directory overview
- `backend/` – FastAPI service code, tests, and (future) migrations.
  - `app/` – API entry point, database helpers, configuration.
  - `tests/` – Pytest suite; currently covers the `/db/ping` health flow.
- `frontend/` – Tailwind-based web client (scaffold ready for future work).
- `infra/` – Dockerfiles, Compose stacks, environment templates.
- `docs/` – Project documentation (including this guide).
- `scripts/` – Utility or automation scripts as they’re added.

## Useful tips
- Update `.env` values carefully; if you change `POSTGRES_DB`, either drop the volume (`docker compose down -v`) or create the new database manually inside the `db` container.
- Health check endpoint: `curl http://localhost:8000/health` should return `{ "status": "ok" }` when the API is running.
- Prefer running commands through Docker to keep local environments consistent.

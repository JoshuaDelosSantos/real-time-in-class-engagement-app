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
   cp .env.example .env
   # edit secrets if needed (POSTGRES_*, etc.)
   ```

## Starting the stack
1. Ensure Docker Desktop is running.
2. From `infra/`, build and start services:
   ```bash
   docker compose up -d --build
   ```
   - FastAPI API runs in the `swampninjas` container on http://localhost:8000.
       Visiting that URL in a browser serves `frontend/public/index.html` by default.
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
- Static assets under `frontend/public/` are mounted into the API container (`FRONTEND_PUBLIC_DIR=/app/frontend/public`) so any edits appear immediately after refreshing the browser.

## Deploying to an Azure VM (containerised)
1. Install Docker on the VM and clone the repository.
2. Populate `infra/.env` with production-ready credentials.
3. Run `docker compose up -d --build` inside `infra/`.
4. Open TCP port `8000` (or the value of `UVICORN_PORT`) on the VM's firewall / NSG.
5. Point a browser to `http://<azure-public-ip>:8000/`—the FastAPI server will deliver `index.html` and the button will call `/health` on the same host.

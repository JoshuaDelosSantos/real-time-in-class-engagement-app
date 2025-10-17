# ClassEngage
ClassEngage is a lightweight, real-time classroom engagement app (inspired by Kahoot) that helps teachers surface the most relevant student questions during live sessions.

## Overview
- **Audience**: One user spins up a session as host; many peers join via a simple code.
- **Primary loop**: Participants submit questions, classmates upvote, and the host resolves the top-voted items.
- **Operating mode**: Near-real-time updates are sufficient—sub-second accuracy is not required.
- **Authentication**: Not required for MVP; users provide a display name when creating or joining a session.
- **Scale expectations**: ~50 concurrent users across multiple sessions.

## Current Capabilities (2025-10-17)
- Docker Compose stack for FastAPI (`swampninjas`) and PostgreSQL with migrations automatically applied at container startup.
- `/health` endpoint returning an API heartbeat and serving `frontend/public/index.html` at the root with a "Press me" demo button.
- `/db/ping` endpoint that exercises PostgreSQL via the repository/service layer and reports insert counts.
- `POST /sessions` endpoint for creating classroom sessions, enforcing host limits, and returning a summary payload.
- `GET /sessions` endpoint for listing recent joinable sessions with optional limit parameter.
- `POST /sessions/{code}/join` endpoint for joining sessions as participants with automatic user creation and role management.
- Comprehensive test suite (50 tests) covering repository, service, API, and integration layers.
- Project documentation including development workflow, dev journal, API specifications, and layered directory READMEs.

## Roadmap Highlights
- Build participant join, question submission, and voting flows on top of the session schema.
- Add WebSocket-based updates and richer frontend interactions.
- Introduce seed data and administrative tooling.
- Layer on analytics, polls, and optional gamification once the core loop is stable.

## Architecture Snapshot
- **Backend**: FastAPI app with routers delegating to services and repositories; Pydantic schemas define API contracts.
- **Persistence**: PostgreSQL (psycopg) with parameterised queries via repository helpers covering users, sessions, session participants, questions, and question votes.
- **Frontend**: Static HTML/CSS prototype served by FastAPI; future-ready for a JS framework.
- **Infrastructure**: Dockerised services aimed at Azure VM deployment with minimal ops overhead.

## Repository Structure
- `backend/`
	- `app/`
		- `api/routes/` — FastAPI routers grouped by feature surface (health checks, session creation).
		- `services/` — Business logic orchestrating repositories.
		- `repositories/` — Data-access helpers using psycopg SQL composition.
		- `schemas/` — Shared Pydantic models.
		- `db.py`, `settings.py`, `main.py` — core application wiring.
	- `tests/` — Pytest suite covering database health checks plus repositories, services, and API flows for session creation.
- `frontend/` — Static assets delivered at `/` with room for future SPA work.
- `infra/` — Dockerfiles, Compose definitions, and environment templates.
- `docs/` — Development guide, dev journal, and supporting documentation.
- `scripts/` — Utility and automation helpers (e.g., migration runner).

## Getting Started
Follow the instructions in [docs/development.md](/docs/development.md) for local setup, testing, and deployment notes. Beginners can also consult the "Development Guide" section in that document to understand where new code should live.
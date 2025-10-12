# Session Creation Plan

## Goal

Enable users (no authentication required) to create classroom sessions via a FastAPI endpoint, ready for frontend integration.

## Scope

- Backend only; no frontend changes.
- Covers migrations, repositories, services, routers, and automated tests required for the `POST /sessions` flow.

## Planned Work

### Database & Migrations

 - `backend/migrations/0001_sessions.sql` (new):
	- Create `users`, `sessions`, and `session_participants` tables matching `docs/data-model.md`.
	- Enforce: unique `sessions.code`, FK constraints, unique `(session_id, user_id)`.
	- Note: host session limits remain a service-layer concern; revisit database enforcement later if needed.
- `scripts/apply_migrations.py` (new): lightweight runner that applies all files under `backend/migrations/` using psycopg.
- `infra/docker-compose.yml`: add the migration runner to the API startup flow (e.g. compose command or entrypoint) so migrations execute automatically in local/dev environments.

### Repository Layer

- `backend/app/repositories/users.py` (new): utilities to fetch or create host records by display name.
- `backend/app/repositories/sessions.py` (new): insert sessions, fetch by `id`/`code`, validate host session cap.
- `backend/app/repositories/session_participants.py` (new): add host participation row during session creation.
- Update `backend/app/repositories/__init__.py` if needed to expose new modules.

### Service Layer

- `backend/app/services/sessions.py` (new/expanded):
	- Accept `SessionCreate`, resolve or create hosts, enforce business rules, generate join codes, wrap repository calls.
	- Return `SessionSummary` with embedded `UserSummary`.
- Introduce shared helpers (e.g. secure join-code generator) if required.

### API Layer

- `backend/app/api/routes/sessions.py` (new): define `POST /sessions` endpoint, returning `SessionSummary`.
- `backend/app/main.py`: register the sessions router with appropriate prefix/tags.
- Ensure dependency injection passes DB pool to the new route.

### Schemas & Settings

- `backend/app/schemas/sessions.py`: confirm the existing models cover new response fields (update only if requirements change).
- `backend/app/settings.py` and `.env`: add configuration knobs (e.g. join-code length) if they emerge during implementation; document changes in `docs/development.md`.

### Testing

- `backend/tests/api/test_sessions.py`: integration test covering happy path for `POST /sessions`.
- `backend/tests/services/test_sessions.py`: service-level tests for business rules (max three active sessions per host, duplicate codes).
- `backend/tests/repositories/test_sessions.py`: repository tests validating inserts and partial index behaviour.
- `backend/tests/conftest.py`: extend fixtures to provide clean DB state and sample users, mirroring the existing `reset_*` helpers used for database integration tests.

### Documentation & Comms

- `backend/app/README.md`: document the new sessions router/service.
- Root `README.md`: update “Current Capabilities” to list the session creation API.
- `docs/data-model.md`: verify alignment (no structural changes expected, note service availability if useful).

## Risks & Follow-ups

- Need to ensure join-code generation handles collisions.
- Confirm display-name capture flow remains sufficient without authentication for identifying hosts.
- Future work: add endpoints for joining sessions, submitting questions, and voting once creation flow is stable.


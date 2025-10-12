# Fetch Sessions Plan

## Goal

Expose a simple way for users visiting the existing homepage (served under the health check) to click a "Fetch sessions" button and see a list of currently available sessions, or a message indicating that none are available.

## Scope

- Backend: add read support for listing sessions through the existing FastAPI stack (repositories → services → API route).
- Frontend: enhance the static homepage to call the new API endpoint and render the response.
- Testing: cover backend query logic and API contract; add a lightweight smoke check for the static page if feasible.

## Planned Work

### Database & Migrations

- No schema changes required; reuse the existing `sessions` table. 
- Optional: add an index on `sessions.created_at DESC` if performance becomes a concern (`CREATE INDEX sessions_created_at_idx ON sessions(created_at DESC);`). Not required for MVP given expected volume.

### Repository Layer

- `backend/app/repositories/sessions.py`: add a `list_sessions(conn, limit: int | None = None)` helper that returns recent sessions ordered by `created_at DESC`, filtered to joinable statuses (`status IN ('draft', 'active')`).
- Update `backend/app/repositories/__init__.py` to expose the new helper if necessary.

### Service Layer

- `backend/app/services/sessions.py`: implement `get_recent_sessions(limit: int | None = None)` orchestrating the repository call and returning `SessionSummary` models.
- Decide whether to include host information in the listing (likely yes, reuse existing schema).

### API Layer

- `backend/app/api/routes/sessions.py`: add `GET /sessions` that accepts an optional `limit` query parameter (default 10), calls the service method, and returns a list of `SessionSummary` objects.
- Ensure empty results return `[]` with `200 OK`.
- Document the default limit and filtering behaviour (draft/active sessions only).

### Frontend (Static Homepage)

- Update `frontend/public/index.html` to add a "Fetch sessions" button and a dedicated results container (separate from the existing health check button/output).
- Add a small script to call `GET /sessions` on button click, render each session (title + code + host display name), and display "No sessions available" when the array is empty.
- Keep styling minimal but readable; reuse existing CSS patterns for consistency.

### Testing

- `backend/tests/repositories/test_sessions_repository.py`: cover the new `list_sessions` helper, verifying ordering and limit handling.
- `backend/tests/services/test_sessions_service.py`: add tests ensuring service returns `SessionSummary` objects and handles empty results.
- `backend/tests/api/test_sessions.py`: extend to cover `GET /sessions` happy path and empty state.
- Optional: add a simple integration test using `TestClient` to ensure the static page loads and includes the placeholder element (can be manual if automation is costly).

### Documentation & Comms

- `docs/api/sessions.md`: document the new `GET /sessions` endpoint alongside the existing POST docs.
- Update `README.md` and relevant package READMEs (API, services, repositories) to mention the fetch capability.
- Note the frontend behaviour in the dev journal entry once implemented.

## Risks & Follow-ups

- Volume of sessions could grow; consider pagination in a follow-up if needed.
- Exposing all sessions publicly might need filtering or status checks when more lifecycle states are introduced.
- Frontend currently static; future SPA work might supersede this implementation, so keep JS lightweight and easy to remove.

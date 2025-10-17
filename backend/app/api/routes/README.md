# API Routes

Router modules live here. Keep logic focused on HTTP concerns and call into services for domain operations.

## Modules

- `health.py` — `/health` heartbeat endpoint.
- `database_health.py` — `/db/ping` database exercise endpoint.
- `sessions.py` — Session management endpoints:
  - `POST /sessions` — Create new classroom sessions
  - `GET /sessions` — List recent joinable sessions
  - `POST /sessions/{code}/join` — Join a session as participant
  
  Maps service exceptions to HTTP status codes (400/404/409/422) and returns `SessionSummary` payloads.

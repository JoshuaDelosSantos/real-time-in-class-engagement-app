# API Routes

Router modules live here. Keep logic focused on HTTP concerns and call into services for domain operations.

## Modules

- `health.py` — `/health` heartbeat endpoint.
- `database_health.py` — `/db/ping` database exercise endpoint.
- `sessions.py` — `POST /sessions` endpoint for creating classroom sessions, mapping service exceptions to 400/409 responses and returning `SessionSummary` payloads.

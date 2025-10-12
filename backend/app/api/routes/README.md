# API Routes

Router modules live here. Keep logic focused on HTTP concerns and call into services for domain operations.

## Modules

- `health.py` — `/health` heartbeat endpoint.
- `database_health.py` — `/db/ping` database exercise endpoint.
- `sessions.py` — `/sessions` endpoint for creating classroom sessions via the service layer.

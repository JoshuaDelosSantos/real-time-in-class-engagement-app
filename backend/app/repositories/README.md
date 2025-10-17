# Repository Layer

Repositories provide focused data-access helpers. They should use parameterised queries and avoid leaking database specifics to callers.

## Modules

- `health_checks.py` — database health check utilities used by the `/db/ping` endpoint.
- `users.py` — create and fetch host/participant records by id or display name.
- `sessions.py` — insert sessions, detect join-code collisions, report host session counts, and list recent joinable sessions.
- `session_participants.py` — manage participant membership for sessions:
  - `add_participant()` — Insert/update participant records with ON CONFLICT handling for idempotency
  - `get_participant()` — Retrieve participant by session and user
  
  Hosts are tracked as participants with `role="host"`; supports role protection logic.

Each helper expects a psycopg connection and returns dictionaries using `dict_row` to keep consumers framework-agnostic.

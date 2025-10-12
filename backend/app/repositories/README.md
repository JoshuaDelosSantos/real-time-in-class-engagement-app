# Repository Layer

Repositories provide focused data-access helpers. They should use parameterised queries and avoid leaking database specifics to callers.

## Modules

- `health_checks.py` — database health check utilities used by the `/db/ping` endpoint.
- `users.py` — create and fetch host/participant records by id or display name.
- `sessions.py` — insert sessions, detect join-code collisions, and report host session counts.
- `session_participants.py` — record or retrieve participant membership for a session (hosts included).

Each helper expects a psycopg connection and returns dictionaries using `dict_row` to keep consumers framework-agnostic.

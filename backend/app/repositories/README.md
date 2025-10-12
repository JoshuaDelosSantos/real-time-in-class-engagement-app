# Repository Layer

Repositories provide focused data-access helpers. They should use parameterised queries and avoid leaking database specifics to callers.

## Modules

- `health_checks.py` — existing database health check utilities.
- `users.py` — create and fetch host/participant records by id or display name.
- `sessions.py` — insert sessions, enforce business rules, and fetch by code/id.
- `session_participants.py` — record or retrieve participant membership for a session.

Each helper expects a psycopg connection and returns dictionaries using `dict_row` to keep consumers framework-agnostic.

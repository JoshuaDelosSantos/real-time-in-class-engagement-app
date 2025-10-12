# Tests

Integration and unit tests for the backend reside here.

- `test_db_ping.py` exercises the `/db/ping` endpoint against a live Postgres instance.
- `api/test_sessions.py` covers the session creation REST endpoint and error scenarios.
- `services/test_sessions_service.py` validates business rules (host limits, code collisions, input sanitisation).
- `repositories/test_sessions_repository.py` ensures repository helpers interact with PostgreSQL as expected.
- `conftest.py` runs migrations, cleans tables between tests, and exposes shared fixtures.

## Running tests
1. cd into the infra/ directory

2. run docker exec command
```
docker compose exec swampninjas pytest
```
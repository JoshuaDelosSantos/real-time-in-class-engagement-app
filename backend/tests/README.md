# Tests

Integration and unit tests for the backend reside here.

- `test_db_ping.py` exercises the `/db/ping` endpoint against a live Postgres instance.
- `api/test_sessions.py` covers the session creation REST endpoint and validation scenarios.
- `services/test_sessions_service.py` validates business rules (host limits, code collisions, input sanitisation).
- `repositories/test_sessions_repository.py` ensures repository helpers interact with PostgreSQL as expected.
- `conftest.py` runs migrations before the suite, cleans tables between tests, and exposes shared fixtures.

## Running tests
From the `infra/` directory you can run tests in either mode:

```
docker compose run --rm swampninjas pytest
```

or, if the stack is already up:

```
docker compose exec swampninjas pytest
```
# Tests

Integration and unit tests for the backend reside here.

- `test_db_ping.py` exercises the `/db/ping` endpoint against a live Postgres instance.
- `conftest.py` adjusts the Python path so tests can import the application package.

Run the suite from the `infra` directory with `docker compose exec swampninjas pytest` once the Docker stack is up.

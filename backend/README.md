# Backend

This directory will house the FastAPI service powering ClassEngage.

- `app/` will contain routers, services, schemas, and core modules.
- `tests/` will collect unit and integration coverage.
- `migrations/` will store database change sets once migration tooling is added.

Refer to the root documentation for setup instructions as they are introduced.

## Running Tests
Ensure the Docker stack is running (the API container named `swampninjas` needs access to the Postgres service). Then execute:

```
docker compose exec swampninjas pytest
```

This integration test exercises the `/db/ping` endpoint, inserting and counting rows in the live Postgres database to verify connectivity end to end.

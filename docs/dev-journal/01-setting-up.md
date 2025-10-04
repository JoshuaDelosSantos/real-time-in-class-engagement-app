## 2025-10-04
- Built the Docker stack (FastAPI container now named `swampninjas` plus Postgres), swapped to a secure base image, added missing deps, fixed database naming/volume issues, and captured the workflow in the docs.
- Implemented `/health` and `/db/ping` endpoints with integration tests hitting Postgres, then wired a simple frontend button to call the health route and served the static assets from FastAPI.
- Refactored into layered API/service/repository modules, added Pydantic schemas and a parameterised repository for DB pings, refreshed the `app` README, and re-ran the test suite to keep everything green.

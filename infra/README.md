# Infra

Infrastructure assets for ClassEngage live here.

- Dockerfiles for services and supporting tooling.
- Compose stacks and deployment manifests targeting the Azure VM.
- Automation scripts for provisioning and environment configuration.

## Local development
- The FastAPI service runs as the `swampninjas` container via `docker compose`.
- PostgreSQL is provided by the `db` service with a persistent `pg_data` volume.
- If you change `POSTGRES_DB` in `.env`, remove the `pg_data` volume (`docker compose down -v`) or create the database manually so the container boots cleanly.

Keep secrets and environment-specific values out of version control.

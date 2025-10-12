# Service Layer

Service modules orchestrate repositories and encapsulate business rules. They should remain free of HTTP-specific details.

## Modules

- `health.py` — returns a static health heartbeat message.
- `database_health.py` — records db health pings via repositories.
- `sessions.py` — coordinates session creation (host lookup/creation, host session-limit enforcement, join-code generation with collision retries).

Services should:
- Accept plain inputs (validated by schemas at the API boundary).
- Use repository helpers for persistence within a single transactional scope.
- Raise domain-specific exceptions so routers can convert them into HTTP responses.

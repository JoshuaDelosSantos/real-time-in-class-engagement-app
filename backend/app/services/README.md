# Service Layer

Service modules orchestrate repositories and encapsulate business rules. They should remain free of HTTP-specific details.

## Modules

- `health.py` — returns a static health heartbeat message.
- `database_health.py` — records db health pings via repositories.
- `sessions.py` — orchestrates session operations:
  - Session creation (host lookup/creation, session-limit enforcement, join-code generation with collision retries)
  - Session listing (fetching recent joinable sessions with host details)
  - Session joining (user lookup/creation, role protection, participant record management)
  
  Raises domain exceptions: `SessionNotFoundError`, `SessionNotJoinableError`, `InvalidDisplayNameError`.

Services should:
- Accept plain inputs (validated by schemas at the API boundary).
- Use repository helpers for persistence within a single transactional scope.
- Raise domain-specific exceptions so routers can convert them into HTTP responses.

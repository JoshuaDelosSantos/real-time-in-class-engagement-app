# API Layer

This package groups the FastAPI router modules that expose HTTP endpoints. Each router should focus on request/response translation and delegate business logic to the service layer.

## Current Endpoints

**Sessions Router** (`routes/sessions.py`):
- POST /sessions — create session
- GET /sessions — list recent sessions
- GET /sessions/{code} — session details
- GET /sessions/{code}/participants — participant roster
- GET /sessions/{code}/questions — list questions (with optional status filter)
- POST /sessions/{code}/questions — submit question (requires X-User-Id header)
- POST /sessions/{code}/join — join session

**Health Router** (`routes/health.py`):
- GET /health/ping — application health check
- GET /health/database — database connectivity check

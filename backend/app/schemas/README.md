# Schemas

Pydantic models and other shared data contracts reside here. They formalise inputs and outputs shared across layers, providing validation, serialization, and type safety for API requests, responses, and internal service contracts.

## Schema Organisation

Each domain entity has its own module with a consistent set of schema variants:

- **`*Base`** — Shared attributes inherited by other schemas (e.g., `UserBase` defines `display_name`).
- **`*Create`** — Request schemas for creating new entities, containing only user-supplied fields.
- **`*Read`** — Complete database representations including all columns (id, timestamps, foreign keys).
- **`*Summary`** — Lightweight versions for nested responses, omitting verbose fields.
- **`*Update`** — Optional-field schemas for partial updates (PATCH operations).

## Available Modules

### `users.py`
Defines user identity and profile schemas.

- `UserBase`, `UserCreate`, `UserRead`, `UserSummary`
- **Validation**: `display_name` must be 1–100 characters.

### `sessions.py`
Defines live classroom session schemas with lifecycle management.

- `SessionBase`, `SessionCreate`, `SessionRead`, `SessionSummary`, `SessionUpdate`, `SessionJoinRequest`
- `SessionStatus` — Literal type: `"draft" | "active" | "ended"`
- **Host Identity**: `host` nests `UserSummary` so clients receive display names in a single response.
- **Creation Flow**: `SessionCreate` accepts `host_display_name`; the service layer resolves or creates the underlying `users` row.
- **Join Flow**: `SessionJoinRequest` accepts only `display_name` (session code comes from URL path); service resolves or creates user and adds participant record with role protection.

### `session_participants.py`
Tracks which users have joined which sessions.

- `SessionParticipantBase`, `SessionParticipantCreate`, `SessionParticipantRead`, `SessionParticipantSummary`
- `ParticipantRole` — Literal type: `"host" | "participant"`
- **Usage**: Created when users join sessions; host row inserted at session creation.
- **Internal Note**: `SessionParticipantCreate` is service-internal; HTTP handlers derive `session_id` from path parameters and `user_id` from auth/session context.

### `questions.py`
Defines question submissions within sessions.

- `QuestionBase`, `QuestionCreate`, `QuestionRead`, `QuestionSummary`, `QuestionUpdate`
- `QuestionStatus` — Literal type: `"pending" | "answered"`
- **Validation**: `body` must be 1–280 characters (matching Twitter-style brevity).
- **Author Identity**: `author` nests `UserSummary` when the question is attributed; remains `None` for anonymous submissions.
- **Session Reference**: `QuestionSummary` includes `session_id` so clients can correlate responses without inspecting request context.

### `question_votes.py`
Tracks upvotes on questions to prevent duplicate likes.

- `QuestionVoteCreate`, `QuestionVoteRead`, `QuestionVoteSummary`, `VoteToggleResult`
- **Special**: `VoteToggleResult` returned by vote endpoints showing `liked` boolean and `total_likes` count.
- **Internal Note**: `QuestionVoteCreate` is constructed within services using request context; clients need not submit these identifiers.

### `health.py`
Health check and monitoring schemas.

- `HealthStatus`, `DatabasePingResult`

## Usage Patterns

### Creating a Session
```python
from datetime import UTC, datetime

from app.schemas import SessionCreate, SessionSummary, UserSummary

# Request body
session_in = SessionCreate(
    title="Introduction to Python",
    host_display_name="Dr. Smith"
)

# Response body
session_out = SessionSummary(
    id=42,
    code="ABC123",
    title="Introduction to Python",
    status="draft",
    host=UserSummary(id=7, display_name="Dr. Smith"),
    created_at=datetime.now(UTC)
)
```

### Submitting a Question
```python
from datetime import UTC, datetime

from app.schemas import QuestionCreate, QuestionSummary, UserSummary

# Request body
question_in = QuestionCreate(
    body="How do decorators work in Python?"
)

# Response body
question_out = QuestionSummary(
    id=101,
    session_id=42,
    body="How do decorators work in Python?",
    status="pending",
    likes=0,
    author=UserSummary(id=15, display_name="Jordan"),
    created_at=datetime.now(UTC)
)
```

### Toggling a Vote
```python
from app.schemas import VoteToggleResult

# Response body after adding a vote
vote_result = VoteToggleResult(
    question_id=101,
    liked=True,
    total_likes=5
)
```

## Design Principles

1. **Validation at the boundary**: All API request schemas enforce length limits and required fields using Pydantic's `Field` with `min_length`/`max_length`.

2. **Type safety with Literals**: Status and role enums use `Literal` types rather than strings, enabling IDE autocomplete and compile-time checking.

3. **Separation of concerns**: Create/Update schemas exclude database-managed fields (id, timestamps); Read schemas include everything; Summary schemas balance detail with response size.

4. **ConfigDict for ORM mode**: Read/Summary schemas use `model_config = ConfigDict(from_attributes=True)` to allow construction from database row objects.

5. **Optional fields for flexibility**: Update schemas and nullable columns (e.g., `QuestionRead.author`, `QuestionRead.answered_at`) use `Optional[T]` to reflect business rules like anonymous submissions or unanswered questions.

## Integration Notes

- Import schemas from the package level: `from app.schemas import SessionCreate, QuestionRead`
- Routers accept `*Create` and `*Update` schemas as request bodies.
- Services return `*Read` or `*Summary` schemas to routers.
- Summaries include nested `UserSummary` objects, so services should hydrate user context before returning data to routers.
- Repositories can accept schema objects or primitives; prefer primitives to avoid tight coupling.
- All timestamps use `datetime` from Python's standard library; ensure database queries return timezone-aware values.

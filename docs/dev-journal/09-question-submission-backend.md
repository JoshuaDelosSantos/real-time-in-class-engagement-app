# Question Submission API — Backend Implementation

## Goal

Implement `POST /sessions/{code}/questions` endpoint allowing authenticated participants to submit questions with backend validation, storage, and retrieval.

## Scope

**Backend Only**: Repository → Service → API layers with critical test coverage.

**Out of Scope**: Frontend UI, character counters, user ID tracking headers (defer to separate ticket).

## Current State

- ✅ Database: `questions` table with indexes on `(session_id, status)` and `(session_id, likes DESC)`
- ✅ Schema: `QuestionCreate` (1-280 chars), `QuestionSummary` with optional author
- ✅ Repository: `list_session_questions()` for reads
- ✅ Service: `SessionService.get_session_questions()` for reads
- ✅ API: `GET /sessions/{code}/questions` with status filtering
- ❌ **Missing**: Write operations (create question, enforce limits)

## Architecture Decisions

### 1. User Identity via Header

**Decision**: Accept `X-User-Id` header for MVP authentication.
- **Why**: Frontend doesn't track user IDs yet; separates concerns
- **Validation**: FastAPI `Header()` with 422 on missing/invalid
- **Future**: Replace with JWT token when auth added

### 2. Question Limit Enforcement

**Decision**: Accept race condition for 3-question limit.
- **Why**: Autocommit connections = no transactions. Fixing requires global refactor (84 tests affected).
- **Mitigation**: Document with TODO, client-side button disabling
- **Future**: Use `SELECT FOR UPDATE` when migrating to transactions

### 3. Service Layer

**Decision**: Extend `SessionService` (not new `QuestionService`).
- **Why**: Questions are session-scoped, matches existing pattern
- **Simplicity**: No circular imports, single service

### 4. Session Status Policy

**Decision**: Allow questions in `draft` and `active` sessions (block `ended`).
- **Why**: Matches join policy, enables pre-class Q&A

## Implementation Plan

### Phase 1: Repository Layer

**File**: `backend/app/repositories/questions.py`

Add functions:
```python
def create_question(conn, session_id: int, author_user_id: int | None, body: str) -> dict
def count_user_pending_questions(conn, session_id: int, user_id: int) -> int
```

**SQL**:
- INSERT with `RETURNING *` for complete record
- COUNT WHERE `session_id = %s AND author_user_id = %s AND status = 'pending'`

**Export**: Update `__init__.py`

**Tests** (3 critical):
1. `test_create_question_with_author` - Success case with user_id
2. `test_create_question_anonymous` - Success with NULL author_user_id
3. `test_count_user_pending_questions` - Verify count logic

---

### Phase 2: Service Layer

**File**: `backend/app/services/sessions.py`

Add exceptions:
```python
class NotParticipantError(RuntimeError): ...
class QuestionLimitExceededError(RuntimeError): ...
```

Add method:
```python
def submit_question(self, *, code: str, user_id: int, body: str) -> QuestionSummary
```

**Logic**:
1. Validate body: strip whitespace, check 1-280 chars, reject empty
2. Get session by code (raise `SessionNotFoundError` if missing)
3. Verify session status is `draft` or `active` (raise `SessionNotJoinableError` if `ended`)
4. Verify user is participant (raise `NotParticipantError`)
5. Get user for display_name (separate `get_user_by_id()` call)
6. Count pending questions (race condition: add TODO comment)
7. Validate count < 3 (raise `QuestionLimitExceededError`)
8. Create question via repository
9. Build and return `QuestionSummary`

**Export**: Update `__init__.py`

**Tests** (5 critical):
1. `test_submit_question_success` - Happy path with author
2. `test_submit_question_session_not_found` - Invalid code
3. `test_submit_question_not_participant` - User not joined
4. `test_submit_question_limit_exceeded` - >= 3 pending questions
5. `test_submit_question_body_validation` - Empty/too long/whitespace

---

### Phase 3: API Layer

**File**: `backend/app/api/routes/sessions.py`

Add endpoint:
```python
@router.post("/{code}/questions", response_model=QuestionSummary, status_code=201)
async def submit_question(
    code: str,
    payload: QuestionCreate,
    user_id: Annotated[int, Header(alias="X-User-Id")]
) -> QuestionSummary
```

**Error Mapping**:
- `SessionNotFoundError` → 404
- `SessionNotJoinableError` → 409 (session ended)
- `NotParticipantError` → 403
- `QuestionLimitExceededError` → 409
- Missing/invalid header → 422 (FastAPI automatic)
- Pydantic validation → 422 (FastAPI automatic)

**Export**: Update service imports

**Tests** (6 critical):
1. `test_post_question_success_201` - Valid submission returns QuestionSummary
2. `test_post_question_missing_user_id_header` - 422 error
3. `test_post_question_session_not_found` - 404 error
4. `test_post_question_not_participant` - 403 error
5. `test_post_question_limit_exceeded` - 409 error
6. `test_post_question_validation_empty_body` - 422 error

---

## Testing Strategy

**Total Critical Tests**: 14 (3 repository + 5 service + 6 API)

**Coverage Focus**:
- Happy path (question created successfully)
- Error boundaries (limits, validation, authorization)
- Edge cases (anonymous, empty body, whitespace)

**Deferred** (non-critical):
- Unicode/emoji handling (Postgres supports by default)
- 280-char boundary testing (Pydantic validates)
- Concurrent submission race condition (documented limitation)
- Transaction rollback (no transactions in use)
- Integration with GET endpoint (existing tests cover)

---

## Implementation Sequence

1. **Repository**: Add `create_question()` + `count_user_pending_questions()` with 3 tests
2. **Service**: Add `submit_question()` method + exceptions with 5 tests
3. **API**: Add POST endpoint with error handling with 6 tests
4. **Verification**: Run full test suite (84 + 14 = 98 tests pass)
5. **Documentation**: Update `docs/api/sessions.md` with POST endpoint spec

**Estimated Time**: 4-6 hours (lean implementation + critical tests only)

---

## API Specification

### POST /sessions/{code}/questions

**Request**:
```http
POST /sessions/ABC123/questions HTTP/1.1
X-User-Id: 42
Content-Type: application/json

{
  "body": "What is the answer to life, universe, and everything?"
}
```

**Success Response** (201):
```json
{
  "id": 123,
  "session_id": 5,
  "body": "What is the answer to life, universe, and everything?",
  "status": "pending",
  "likes": 0,
  "author": {
    "id": 42,
    "display_name": "Alice"
  },
  "created_at": "2025-10-30T12:34:56Z"
}
```

**Error Responses**:
| Code | Condition | Message |
|------|-----------|---------|
| 422 | Missing X-User-Id | FastAPI validation error |
| 422 | Body empty/too long | Pydantic validation error |
| 404 | Session not found | "Session not found" |
| 403 | Not participant | Custom error message |
| 409 | Limit exceeded | "User has reached question limit" |
| 409 | Session ended | "Session has ended" |

---

## Race Condition Documentation

**Location**: `backend/app/services/sessions.py` in `submit_question()`

**Comment**:
```python
# TODO: Race condition possible with autocommit connections.
# Count + insert not atomic. Two concurrent submissions may exceed limit.
# Fix: Wrap in transaction with SELECT FOR UPDATE when migrating away from autocommit.
# Risk: Low (requires exact concurrent timing from same user).
# Mitigation: Client-side button disabling reduces likelihood.
```

---

## Success Criteria

- ✅ POST endpoint accepts X-User-Id header and QuestionCreate body
- ✅ Returns 201 with QuestionSummary on success
- ✅ Enforces 3-question limit per user per session
- ✅ Blocks submissions to ended sessions
- ✅ Blocks non-participants
- ✅ Validates body length (1-280 chars)
- ✅ 14 critical tests pass
- ✅ 84 existing tests remain passing
- ✅ Race condition documented with TODO

---

## Out of Scope (Future Work)

- Frontend implementation (UI form, character counter, error display)
- User ID tracking headers (`X-Created-User-Id` in join/create responses)
- sessionStorage augmentation
- CSS styling
- Manual frontend testing
- Integration tests for full submit → GET flow
- WebSocket notifications for real-time updates
- Question editing/deletion
- Host moderation (mark as answered)

**Next**: Frontend ticket to consume this API (separate dev journal entry).

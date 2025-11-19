# Question Submission API — Backend Implementation

## Goal

Implement `POST /sessions/{code}/questions` endpoint for question submission with backend validation, storage, and limit enforcement.

**Note**: Question viewing (`GET /sessions/{code}/questions`) already exists and is fully functional.

## Scope

**This Plan Implements**:
- POST endpoint for question submission
- Repository write operations (create, count)
- Service layer validation and orchestration
- Critical test coverage (14 tests)

**Prerequisites** (Must be done first or in parallel):
- Frontend must send `X-User-Id` header (user ID tracking not yet implemented)
- Alternative: Accept `display_name` in request body as interim solution

**Out of Scope**: 
- Frontend UI, character counters
- User ID tracking headers in join/create responses (separate effort)
- Question editing/deletion
- Host moderation features

## Current State

- ✅ Database: `questions` table with indexes
- ✅ Schemas: `QuestionCreate`, `QuestionSummary` 
- ✅ Repository: `list_session_questions()` for reads
- ✅ Service: `SessionService.get_session_questions()` for reads
- ✅ **API: `GET /sessions/{code}/questions` with status filtering (ALREADY IMPLEMENTED)**
- ❌ **Missing**: Write operations (create question, enforce limits)

## Architecture Decisions

### 1. User Identity Strategy

**Problem**: Frontend doesn't track user IDs in sessionStorage yet.

**Options**:
1. **X-User-Id header** - Requires frontend changes (NOT backend-only)
2. **display_name in body** - Look up user by name (extra query, name conflicts possible)
3. **Block until frontend ready** - Delays feature

**Decision**: **Option 1** - Accept `X-User-Id` header
- **Why**: Clean separation, matches future auth pattern
- **Caveat**: Frontend must be updated to send this header (see Prerequisites)
- **Interim**: Frontend team must implement user ID tracking FIRST or in parallel
- **Validation**: FastAPI `Header()` with 422 on missing/invalid
- **Future**: Replace with JWT token when auth added

**Truth**: This is NOT truly "backend only"—frontend changes are required for this endpoint to function.

### 2. Question Limit Enforcement

**Decision**: Accept race condition for 3-question limit.
- **Why**: Autocommit connections = no transactions. Fixing requires global refactor.
- **Mitigation**: Document with TODO comment at count check, client-side button disabling
- **Future**: Use `SELECT FOR UPDATE` in transaction when migrating away from autocommit

### 3. Service Layer Organization

**Decision**: Extend `SessionService` (not new `QuestionService`).
- **Why**: Questions are session-scoped, matches existing pattern
- **Simplicity**: No circular imports, single service

### 4. Session Status Policy & Exception Handling

**Decision**: Allow questions in `draft` and `active` sessions (block `ended`).
- **Why**: Matches join policy, enables pre-class Q&A
- **Exception Choice**: Reuse `SessionNotJoinableError` for consistency with join flow
- **Note**: This exception name is slightly misleading for questions but maintains consistency

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
4. Verify user is participant via `get_participant()` (raise `NotParticipantError` if None)
5. Get user for display_name via separate `get_user_by_id()` call
6. Count pending questions with `count_user_pending_questions()`
7. **Race condition point**: Add TODO comment HERE before validation
8. Validate count < 3 (raise `QuestionLimitExceededError` if >= 3)
9. Create question via `create_question()` repository call
10. Build and return `QuestionSummary` with author details

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
4. **Verification**: Run full test suite to ensure no regressions
5. **Documentation**: Update `docs/api/sessions.md` with POST endpoint spec

**Estimated Time**: 4-6 hours (lean implementation + critical tests only)

**Note**: Frontend changes (user ID tracking) must happen in parallel or this endpoint will be non-functional.

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

**Location**: `backend/app/services/sessions.py` in `submit_question()` method

**Exact placement** (between count and validation):
```python
def submit_question(self, *, code: str, user_id: int, body: str) -> QuestionSummary:
    # ... session lookup, participant check, user lookup ...
    
    # Count pending questions for this user in this session
    count = count_user_pending_questions(conn, session["id"], user_id)
    
    # TODO: Race condition possible with autocommit connections.
    # Count + insert not atomic. Two concurrent submissions may exceed limit.
    # Fix: Wrap in transaction with SELECT FOR UPDATE when migrating away from autocommit.
    # Risk: Low (requires exact concurrent timing from same user).
    # Mitigation: Client-side button disabling reduces likelihood.
    if count >= 3:
        raise QuestionLimitExceededError("User has reached question limit")
    
    # Create question...
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
- ✅ All existing tests remain passing
- ✅ Race condition documented with TODO at exact location
- ⚠️ **Caveat**: Endpoint unusable until frontend sends X-User-Id header

---

## Known Limitations

1. **Frontend Dependency**: This endpoint requires frontend to send X-User-Id header. Frontend changes must happen in parallel:
   - Add X-Created-User-Id to join/create API responses
   - Store userId in sessionStorage
   - Send X-User-Id header in question submission requests

2. **Race Condition**: 3-question limit can be exceeded with exact concurrent timing (documented with TODO)

3. **Exception Naming**: `SessionNotJoinableError` used for both join operations and question submissions (slightly misleading but maintains consistency)

---

## Out of Scope (Future Work)

- **Frontend user ID tracking** (required for endpoint to function—separate ticket needed)
- Frontend UI form, character counter, error display
- sessionStorage augmentation with userId
- CSS styling for question form
- Manual frontend testing
- Integration tests for full submit → GET flow
- WebSocket notifications for real-time updates
- Question editing/deletion
- Host moderation (mark as answered, delete questions)

**Critical Next Step**: Frontend must implement user ID tracking before this endpoint is usable in production.

---

## API Endpoints Summary

| Method | Path | Status |
|--------|------|--------|
| GET | `/sessions/{code}/questions` | ✅ **ALREADY IMPLEMENTED** (question viewing) |
| POST | `/sessions/{code}/questions` | ❌ **TO BE IMPLEMENTED** (question submission) |

Both endpoints work together to provide complete question functionality.

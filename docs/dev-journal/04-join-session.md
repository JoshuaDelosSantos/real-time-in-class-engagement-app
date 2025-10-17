# Join Session Backend — Planning & Implementation Log

## Goal

Implement backend API endpoint `POST /sessions/{code}/join` that validates a session code, creates or retrieves a user by display name, and creates a participant record, returning session details.

## Gap Analysis

### What Exists Today

1. **Database Schema** ✓
   - `session_participants` table with proper constraints
   - `users` table for user records
   - `sessions` table with join codes

2. **Repository Layer** ✓ (Complete, Needs Test Coverage)
   - `add_participant()` — inserts/updates participant records (existing, untested)
   - `get_participant()` — retrieves participant by session/user (existing, untested)
   - `get_user_by_display_name()` — finds existing users
   - `create_user()` — creates new user records
   - `get_session_by_code()` — validates session codes

3. **Schemas** ⚠️ (Partial Conflict)
   - `SessionJoin` exists but has both `code` and `display_name` (not used anywhere)
   - `SessionSummary` for response payloads ✓
   - `ParticipantRole` enum ✓

### What's Missing

1. **Service Layer** ✗
   - No `join_session()` orchestration method
   - Helper `_get_or_create_host()` is semantically wrong for participants (should be `_get_or_create_user()`)

2. **API Endpoint** ✗
   - No `POST /sessions/{code}/join` route

3. **Schemas** ⚠️
   - Need to replace `SessionJoin` with `SessionJoinRequest` (display_name only)
   - Current `SessionJoin` has code duplication (path + body) which violates RESTful convention

4. **Testing** ✗
   - No test coverage for `add_participant()` and `get_participant()` repository functions
   - No coverage for join flow at service/API layers

5. **Documentation** ✗
   - API docs incomplete (no join endpoint documented)

## Implementation Approach

### Service Layer (`backend/app/services/sessions.py`)

**Refactor existing code**:
- Rename `_get_or_create_host()` → `_get_or_create_user()` for semantic accuracy
- Update `create_session()` to use renamed helper

**Add `join_session()` method to `SessionService`**:

**Responsibilities**:
- Validate display name (non-empty, trim whitespace)
- Look up session by code
- Verify session exists (raise `SessionNotFoundError` if not)
- Verify session is joinable: `status IN ('draft', 'active')` (raise `SessionNotJoinableError` if ended)
- Get or create user record by display name
- **Role protection**: If user is session host, maintain role="host"; otherwise role="participant"
- Create participant record with appropriate role
- Fetch host details and return complete `SessionSummary`

**New Exceptions**:
- `SessionNotFoundError(RuntimeError)` — "Session not found"
- `SessionNotJoinableError(RuntimeError)` — "Session has ended and is no longer joinable"
- Reuse `InvalidDisplayNameError` — "Display name is required"

### API Layer (`backend/app/api/routes/sessions.py`)

Add endpoint: `POST /sessions/{code}/join`

**Request**:
- Path param: `code` (string)
- Body: `SessionJoinRequest` with `display_name` field only

**Response Codes**:
- `200 OK` — Returns `SessionSummary` (successful join)
- `400 BAD_REQUEST` — Whitespace-only display name (service validation)
- `404 NOT_FOUND` — Session not found
- `409 CONFLICT` — Session not joinable (ended status)
- `422 UNPROCESSABLE_ENTITY` — Empty/null display name (Pydantic validation)

**Error Handling**:
```python
try:
    return service.join_session(code=code, display_name=payload.display_name)
except InvalidDisplayNameError as exc:
    raise HTTPException(status_code=400, detail=str(exc))
except SessionNotFoundError as exc:
    raise HTTPException(status_code=404, detail=str(exc))
except SessionNotJoinableError as exc:
    raise HTTPException(status_code=409, detail=str(exc))
```

### Schema (`backend/app/schemas/sessions.py`)

**Replace** `SessionJoin` with `SessionJoinRequest`:
- Remove `SessionJoin` class (unused, has code duplication issue)
- Add `SessionJoinRequest` with only `display_name: str` field (min_length=1, max_length=100)
- Update `__init__.py` exports to remove `SessionJoin`, add `SessionJoinRequest`

### Testing Strategy

**Repository Tests** (`backend/tests/repositories/test_session_participants.py` - create new file):
- **Note**: `add_participant()` and `get_participant()` already exist but lack test coverage
- Add participant successfully (basic insert)
- **ON CONFLICT behavior**: Adding same user to same session updates role (idempotent)
- Get participant returns correct record
- Get non-existent participant returns None
- Foreign key constraints enforced (invalid session_id/user_id raises error)

**Service Tests** (`backend/tests/services/test_sessions_service.py` - extend existing):
- Join session with new user (creates user + participant)
- Join session with existing user (reuses user, creates participant)
- Join same session twice with same user (idempotent, returns session)
- Join draft session succeeds
- Join active session succeeds
- **Join ended session raises `SessionNotJoinableError`** (use direct SQL to set status='ended')
- Join with invalid code raises `SessionNotFoundError`
- Join with whitespace-only display name raises `InvalidDisplayNameError`
- **Host joining own session maintains role="host"** (critical: prevents role downgrade)
- Non-host joining session gets role="participant"
- Response includes correct session and host details

**API Tests** (`backend/tests/api/test_sessions.py` - extend existing):
- Valid join returns 200 + SessionSummary
- Invalid code returns 404
- Ended session returns 409
- Whitespace-only display name returns 400 (service validation)
- **Empty/null display name returns 422** (Pydantic validation)
- Response includes session title, code, status, and host info

**Integration Tests** (`backend/tests/integration/test_join_flow.py` - create new file):
- End-to-end: Create session via API → Join as participant via API → Query DB to verify participant record
- Multiple participants join same session (verify all stored correctly)
- Host joining own session via API maintains host role
- Idempotent joins: same user joins twice, DB has single participant record

## Implementation Plan

### Phase 1: Refactor & Service Layer
1. **Refactor**: Rename `_get_or_create_host()` → `_get_or_create_user()` in SessionService
2. Update `create_session()` to use renamed helper
3. Add new exception classes (`SessionNotFoundError`, `SessionNotJoinableError`)
4. Implement `join_session()` method with role protection logic
5. Update service exports in `__init__.py`

### Phase 2: Schema Updates
6. **Replace** `SessionJoin` with `SessionJoinRequest` (display_name only)
7. Update `backend/app/schemas/__init__.py` exports
8. Verify no code references old `SessionJoin` (should be none)

### Phase 3: API Layer
9. Add `POST /sessions/{code}/join` endpoint in routes
10. Wire up error handling for all exception types (400, 404, 409, 422)

### Phase 4: Testing - Repository Layer
11. Create `backend/tests/repositories/test_session_participants.py`
12. Write tests for existing `add_participant()` function:
    - Basic insert success
    - ON CONFLICT behavior (idempotency)
    - Foreign key constraint validation
13. Write tests for existing `get_participant()` function:
    - Successful retrieval
    - Non-existent participant returns None

### Phase 5: Testing - Service Layer
14. Extend `backend/tests/services/test_sessions_service.py`
15. Add ~10 test cases for `join_session()`:
    - New user join
    - Existing user join
    - Idempotent join (same user twice)
    - Draft/active session success
    - **Ended session rejection** (use SQL UPDATE to set status='ended')
    - Invalid code rejection
    - Whitespace display name rejection
    - **Host role protection** (host joining maintains role)
    - **Participant role assignment** (non-host gets role="participant")
    - Response validation

### Phase 6: Testing - API Layer
16. Extend `backend/tests/api/test_sessions.py`
17. Add ~6 test cases for join endpoint:
    - Valid join returns 200 + SessionSummary
    - Invalid code returns 404
    - Ended session returns 409
    - Whitespace display name returns 400
    - **Empty/null display name returns 422**
    - Response structure validation

### Phase 7: Testing - Integration
18. Create `backend/tests/integration/test_join_flow.py`
19. Add end-to-end tests:
    - Create session → Join as participant → Verify DB state
    - Multiple participants join same session
    - Host joins own session → Verify role="host" maintained
    - Idempotent joins → Verify single DB record

### Phase 8: Documentation
20. Update `docs/api/sessions.md` with join endpoint specification
21. Document error codes, request/response examples, edge cases
22. Record implementation outcomes in this dev journal

## Key Decisions

### 1. Schema Design - Replace, Don't Extend
**Decision**: Replace existing `SessionJoin` with `SessionJoinRequest` (display_name only).  
**Rationale**: Current `SessionJoin` duplicates code in path and body, violating RESTful convention. It's unused in codebase, so safe to replace. Resource identifiers belong in URL path, not request body.

### 2. Helper Function Refactor
**Decision**: Rename `_get_or_create_host()` → `_get_or_create_user()`.  
**Rationale**: Function is semantically neutral (just gets/creates user record), not host-specific. Used by both host creation and participant joining. Private function (`_` prefix) means no external callers to break. Makes codebase more honest about what the function does.

### 3. Validation Error Codes
**Decision**: 422 for empty/null display name (Pydantic); 400 for whitespace-only (service).  
**Rationale**: Pydantic's `min_length=1` catches empty strings before service layer. Service validates business rule (no whitespace-only names). Different error codes help distinguish validation source.

### 4. Host Role Protection - Critical
**Decision**: When host joins own session, maintain `role="host"` not `role="participant"`.  
**Rationale**: Prevents accidental role downgrade. Repository `ON CONFLICT DO UPDATE` would overwrite role if not handled. Check if `user_id == session.host_user_id` and preserve host role. **This is a critical bug fix** - without it, host could lose privileges.

### 5. Idempotency Design
**Decision**: Joining same session twice returns success without error.  
**Rationale**: Database `ON CONFLICT DO UPDATE` handles duplicates gracefully. Enables seamless reconnect/refresh experience. No application error needed.

### 6. Display Name Uniqueness
**Decision**: Display names are not globally unique; multiple users can use same name.  
**Rationale**: Simplifies MVP UX (no "username already taken" errors). Each join creates/reuses user record by name. Future authentication will provide true unique identifiers.

### 7. Joinable Session Statuses
**Decision**: Only "draft" and "active" sessions joinable; "ended" returns 409 Conflict.  
**Rationale**: Draft allows pre-session joins; active is primary use case; ended sessions are closed to new participants. 409 signals conflict with session state.

### 8. Testing Ended Sessions
**Decision**: Use direct SQL UPDATE in tests to create ended session scenario.  
**Rationale**: No `end_session()` service method exists yet. Adding one now is scope creep. Direct DB manipulation is acceptable in tests and explicit about state setup.

### 9. Anonymous Access
**Decision**: No authentication required for MVP; users identified by display name per session.  
**Rationale**: Reduces friction for classroom use. Focus on core functionality first. Future iterations will add proper auth.

## Success Criteria

- [ ] **Refactor**: `_get_or_create_host()` renamed to `_get_or_create_user()`
- [ ] **Schema**: `SessionJoin` replaced with `SessionJoinRequest` (display_name only)
- [ ] **API**: `POST /sessions/{code}/join` endpoint implemented and working
- [ ] **Join Flow**: Participant can join session with valid code and display name
- [ ] **Database**: System creates participant record with correct role
- [ ] **Idempotency**: Duplicate joins handled gracefully (same user → same session works)
- [ ] **Errors**: Invalid codes return 404 with "Session not found"
- [ ] **Errors**: Ended sessions return 409 with "Session has ended and is no longer joinable"
- [ ] **Errors**: Whitespace display names return 400 with "Display name is required"
- [ ] **Errors**: Empty/null display names return 422 (Pydantic validation)
- [ ] **Role Protection**: Host joining own session maintains role="host" (not downgraded)
- [ ] **Role Assignment**: Non-host joining session gets role="participant"
- [ ] **Response**: Returns complete SessionSummary with host details
- [ ] **Repository Tests**: Pass for add_participant, get_participant (ON CONFLICT, foreign keys)
- [ ] **Service Tests**: Pass ~10 test cases covering all edge cases
- [ ] **API Tests**: Pass ~6 test cases covering all HTTP responses
- [ ] **Integration Tests**: Pass end-to-end flow with DB verification
- [ ] **Documentation**: `docs/api/sessions.md` updated with join endpoint spec
- [ ] **Code Quality**: Follows existing patterns and conventions

## Known Limitations & Trade-offs

- **Display name collisions**: Multiple users can use same display name (acceptable for MVP, fixed by auth)
- **No session persistence**: Browser session only (no cookies/tokens for returning users)
- **Spam joins**: Each join creates user record (future: rate limiting, user deduplication)
- **No capacity limits**: Sessions can have unlimited participants (future: configurable max)
- **API only**: No frontend implementation in this phase (deliberate scope constraint)
- **Direct SQL in tests**: Using UPDATE to test ended sessions (acceptable, explicit test setup)
- **Error message hardcoding**: Exception messages defined in code (future: i18n/centralized messages)

## Critical Implementation Notes

### Host Role Protection Logic
```python
# Pseudo-code for service layer
session = get_session_by_code(conn, code)
user = _get_or_create_user(conn, display_name)

# CRITICAL: Check if user is the session host
if user["id"] == session["host_user_id"]:
    role = "host"  # Maintain host privileges
else:
    role = "participant"  # Regular participant

add_participant(conn, session_id=session["id"], user_id=user["id"], role=role)
```

### Error Message Definitions
- `SessionNotFoundError`: "Session not found"
- `SessionNotJoinableError`: "Session has ended and is no longer joinable"
- `InvalidDisplayNameError`: "Display name is required" (reuse existing)

### Testing Ended Sessions
```python
# In test setup - direct SQL manipulation
with db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE sessions SET status = 'ended' WHERE code = %s",
            (session_code,)
        )
```

## Follow-up Work

1. **Frontend Join Form**: Add UI on landing page to call join endpoint
2. **Session Page**: Dedicated view showing session details after join
3. **Questions & Voting API**: Backend for question submission and voting
4. **Questions & Voting UI**: Frontend for question/voting interaction
5. **WebSocket Integration**: Real-time updates for participants and questions
6. **Participant Roster API**: Endpoint to list all session participants
7. **Authentication**: Replace display names with proper user accounts and sessions
8. **Rate Limiting**: Prevent spam joins (per-IP or per-session throttling)
9. **Session Capacity**: Configurable participant limits per session
10. **Host Controls API**: Start, pause, end session endpoints


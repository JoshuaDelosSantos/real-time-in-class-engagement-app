# Question Submission — Planning & Implementation Log

## Goal

Implement question submission feature allowing participants to submit questions during live sessions, with backend validation, storage, and frontend UI.

## Context

**Current State**:
- Session creation, joining, and detail viewing work end-to-end
- Session page displays participant roster and question feed (read-only)
- Question database schema exists with all constraints and indexes
- `QuestionCreate` schema exists for submission validation
- `list_session_questions()` repository function exists for retrieval
- No endpoint or UI for submitting questions
- **Critical Gap**: User ID not tracked in frontend sessionStorage

**Why This Matters**:
Questions are the core interaction in ClassEngage. Without submission capability, the session page is a static view with no participant engagement. This feature unlocks the primary use case: students asking questions during class.

## Architecture Decisions

### Decision 1: User Identity Strategy

**Problem**: Frontend needs to know current user's ID to submit questions, but it's not currently stored.

**Options Considered**:
1. **Pass display_name, look up user server-side** - Requires extra DB query per submission
2. **Return user_id in response body** - Breaking change affects 10+ files
3. **Return user_id in response header** - Non-breaking, RESTful pattern
4. **Use browser fingerprinting** - Complex, unreliable

**Decision**: **Option 3** - Return user ID in custom response header `X-Created-User-Id`
- **Zero breaking changes**: Response body unchanged, existing tests unaffected
- **RESTful pattern**: Headers for metadata (like Location, ETag)
- **Backwards compatible**: Old clients ignore header, works immediately
- **Upgrade path**: Header removed when proper authentication added
- **Implementation**: 
  - Backend adds header to join/create responses
  - Frontend reads `response.headers.get('X-Created-User-Id')`
  - sessionStorage augmented: `{...session, userId}`

### Decision 2: Get Participant Data Structure

**Problem**: `get_participant()` returns limited fields, no display_name for building author summaries.

**Options Considered**:
1. **Add JOIN to users table in get_participant()** - Single query, complete data
2. **Separate call to get_user_by_id()** - Two queries, more flexible
3. **Pass display_name from frontend** - No extra query but less secure

**Decision**: **Option 2** - Separate user lookup
- Rationale: `get_participant()` is focused on participation data, not user profiles
- Separation of concerns: participant repository handles session_participants, user repository handles users
- No breaking changes: existing callers unaffected
- Trade-off: One extra query acceptable for question submission (not high-frequency operation)

### Decision 3: Service Layer Organization

**Problem**: Question logic needs exceptions from sessions service, risk of circular imports.

**Options Considered**:
1. **Create services/questions.py, import from sessions** - Clean separation
2. **Add question methods to SessionService** - Single service, simpler imports
3. **Create shared exceptions module** - Most flexible, most overhead

**Decision**: **Option 2** - Extend SessionService with question methods
- Rationale: Questions are inherently session-scoped (always require session context)
- Simpler: No new service files, no import complexity
- Consistent: Matches existing pattern (get_session_questions already in SessionService)
- Future: Can split later if question logic grows significantly

### Decision 5: Question Limit Enforcement

**Problem**: With autocommit=True connections, counting pending questions then inserting is not atomic. Two concurrent submissions can both pass validation and exceed the 3-question limit.

**Options Considered**:
1. **Transaction with SELECT FOR UPDATE** - Requires removing autocommit globally (affects all 84 tests)
2. **Pessimistic locking** - Requires transactions
3. **Optimistic locking with retry** - Complex, eventual consistency issues
4. **Database constraint** - Not possible (Postgres can't constraint on conditional count)
5. **Accept race condition as MVP limitation** - Document clearly, fix when refactoring transactions

**Decision**: **Option 5** - Accept race condition with explicit documentation
- **Why**: Risk of global autocommit change exceeds benefit of fixing soft limit
- **Trade-off**: Race window is milliseconds, requires exact concurrent timing
- **Mitigation**: Client-side submit button disabling reduces likelihood
- **Documentation**: Clear TODO comment explaining race condition and future fix with transaction
- **Upgrade path**: When removing autocommit (separate refactor), replace with `SELECT FOR UPDATE`

### Decision 4: Session Status Policy

**Problem**: Should draft sessions accept questions, or only active sessions?

**Options Considered**:
1. **Draft + Active** - Flexible, allows pre-class Q&A
2. **Active only** - Stricter, requires explicit session start
3. **All statuses** - Too permissive

**Decision**: **Option 1** - Allow questions in draft and active sessions
- Rationale: Matches current join policy (can join draft or active)
- Use case: Students can submit questions while teacher is setting up
- Simplicity: Same status check as join flow
- Ended sessions still blocked: prevents questions after class concludes

### Decision 6: CSS Styling Strategy

**Problem**: Plan needs colors for character counter states. Codebase uses hex codes, not CSS variables.

**Options Considered**:
1. **Add CSS custom properties first** - Better architecture, more upfront work
2. **Use existing hex codes** - Matches codebase, faster delivery
3. **Mix both approaches** - Confusing, inconsistent

**Decision**: **Option 2** - Use hex codes directly, add TODO for future refactor
- **Why**: Feature delivery > architectural perfection for MVP
- **Consistency**: Matches existing codebase (31 hex colors in styles.css)
- **Maintainability**: Grep-able colors, easy to find/replace in dedicated refactor
- **Upgrade path**: Can extract to CSS variables in separate styling sprint

### Decision 7: Question Form Placement

**Problem**: session.html has no dedicated container div for question form. Plan assumes `question-form-container` exists.

**Options Considered**:
1. **Add container div to HTML** - Requires HTML modification
2. **Programmatic injection before question feed** - Leverages existing structure
3. **Append to body** - Poor UX, layout fragility

**Decision**: **Option 2** - Inject form dynamically before `#questions-feed`
- **Why**: Minimises HTML changes, form is ephemeral UI
- **Maintainability**: Form rendering logic lives in session.js with related code
- **Upgradeability**: Easy to conditionally render based on permissions when auth added
- **Implementation**: `document.getElementById('questions-feed').insertAdjacentHTML('beforebegin', formHTML)`

## Gap Analysis

### What Exists Today

1. **Database Schema** ✓
   - `questions` table with all fields (id, session_id, author_user_id, body, status, likes, created_at, answered_at)
   - `author_user_id` nullable for anonymous submissions
   - `body` length constraint handled at application layer (1-280 chars)
   - Status defaults to 'pending'
   - Indexes on `(session_id, status)` and `(session_id, likes DESC)`

2. **Schemas** ✓ (Complete)
   - `QuestionCreate` with `body` field (min_length=1, max_length=280)
   - `QuestionSummary` for API responses with optional author
   - `UserSummary` for embedding author details
   - Already exported from `backend/app/schemas/__init__.py`

3. **Repository Layer** ⚠️ (Partial)
   - `list_session_questions()` exists for reading questions
   - Need: `create_question()` function for inserting new questions
   - Need: `count_user_pending_questions()` for enforcing 3-question limit

4. **Service Layer** ✗
   - No `submit_question()` method
   - No business logic for enforcing question limits
   - No validation for session status (can't submit to ended sessions)

5. **API Endpoint** ✗
   - No `POST /sessions/{code}/questions` route

6. **Frontend** ⚠️ (Partial)
   - Session page displays questions (read-only)
   - No question submission form
   - No API function for submitting questions
   - Need: UI component for question input

### What's Missing

1. **Repository Functions** (`backend/app/repositories/questions.py`)
   - `create_question(conn, session_id, author_user_id, body)` → Insert question, return full record
   - `count_user_pending_questions(conn, session_id, user_id)` → Count for limit enforcement

2. **Service Layer** (`backend/app/services/sessions.py` or new `backend/app/services/questions.py`)
   - `submit_question(session_code, user_id, body)` → Orchestrate validation and creation
   - Responsibilities:
     - Look up session by code
     - Validate session exists (raise `SessionNotFoundError`)
     - Validate session is active (raise `SessionNotActiveError` if draft/ended)
     - Validate user is participant (raise `NotParticipantError`)
     - Enforce question limit (raise `QuestionLimitExceededError` if >= 3 pending)
     - Validate question body (raise `InvalidQuestionBodyError` if empty/too long)
     - Create question with author_user_id
     - Fetch and return `QuestionSummary`

3. **API Route** (`backend/app/api/routes/sessions.py`)
   - `POST /sessions/{code}/questions` endpoint
   - Path param: `code` (session code)
   - Body: `QuestionCreate` with `body` field
   - Header: User identity (from sessionStorage, passed as `X-User-Id` header for MVP)
   - Response: `QuestionSummary` (201) or error (400, 403, 404, 409)

4. **Frontend API** (`frontend/public/js/api.js`)
   - `submitQuestion(code, body, userId)` → POST to endpoint with user context

5. **Frontend UI** (`frontend/public/js/session.js`)
   - Question submission form component
   - Character counter (280 char limit)
   - Submit button with loading state
   - Success feedback (show new question in feed)
   - Error handling with user-friendly messages

6. **Testing**
   - Repository tests for `create_question()` and `count_user_pending_questions()`
   - Service tests for business logic (limits, validation, error cases)
   - API integration tests for POST endpoint
   - Manual frontend testing

## Implementation Plan

### Phase 1: User ID Tracking (Non-Breaking Solution)

**Backend Changes**:
1. Modify `POST /sessions/{code}/join` endpoint in `api/routes/sessions.py`:
   - Add response header: `X-Created-User-Id: {user_id}`
   - Keep response body unchanged (SessionSummary)
2. Modify `POST /sessions` endpoint (create):
   - Add response header: `X-Created-User-Id: {session.host.id}`
   - Keep response body unchanged (SessionSummary)

**Frontend Changes** (`frontend/public/js/`):
1. Update `api.js`:
   - `joinSession()`: Return full Response object, not just JSON
   - `createSession()`: Return full Response object
2. Update `ui.js`:
   - `renderJoinSuccess()`: Extract userId from `response.headers.get('X-Created-User-Id')`
   - Store augmented session: `sessionStorage.setItem('currentSession', JSON.stringify({...session, userId}))`
   - `renderCreateSuccess()`: Extract userId from header
   - Store augmented session
3. Update `session.js`:
   - `getCurrentUser()`: Return `JSON.parse(sessionStorage.getItem('currentSession'))?.userId`

**Tests**: Verify header presence, sessionStorage structure (augmented, not replaced).

**Key Benefits**:
- Zero breaking changes (existing tests pass)
- Backwards compatible (old clients ignore header)
- Clean upgrade path (remove header when auth added)

---

### Phase 2: Repository Layer

**File**: `backend/app/repositories/questions.py`

Add:
1. `create_question(conn, session_id, author_user_id, body)` → dict
2. `count_user_pending_questions(conn, session_id, user_id)` → int

**Key SQL**: COUNT WHERE `status = 'pending'`

Update `__init__.py` exports.

**Tests** (6): Success, anonymous, validation, 280-char, unicode, rollback.

---

### Phase 3: Service Layer

**File**: `backend/app/services/sessions.py`

Add exceptions: `NotParticipantError`, `QuestionLimitExceededError`, `InvalidQuestionBodyError`

Add method: `SessionService.submit_question(session_code, user_id, body) → QuestionSummary`

**Logic**: 
1. Trim/validate body (empty, too long, whitespace-only)
2. Look up session by code
3. Check user is participant
4. Get user display_name via separate `get_user_by_id()` call
5. Count pending questions with `count_user_pending_questions()`
6. **Race Condition Note**: Count + insert not atomic due to autocommit=True
   - Add explicit TODO comment: "Race condition possible: concurrent submissions may exceed limit. Fix when migrating to transactions with SELECT FOR UPDATE."
   - Mitigation: Client-side button disabling, small time window
7. Create question with `create_question()`
8. Build and return QuestionSummary

**Key nuance**: Separate `get_participant()` and `get_user_by_id()` calls maintain repository separation.

Update `__init__.py` exports.

**Tests** (11): Success, exceptions, body validation, schema, race condition documentation check.

---

### Phase 4: API Endpoint

**File**: `backend/app/api/routes/sessions.py`

Add: POST `/sessions/{code}/questions`

**Request**: code (path), X-User-Id (header), QuestionCreate (body)

**Response**: 201 QuestionSummary | 400/403/404/422 errors

**Key nuance**: `user_id: int = Header(..., alias="X-User-Id")`

**Tests** (12): 201 success, missing header, not participant, limit exceeded, not found, validation, schema, feed integration.

---

### Phase 5: Frontend API

**File**: `frontend/public/js/api.js`

Add `submitQuestion(code, body, userId)`: POST with `X-User-Id` header.

**Tests**: Manual - header injection, error parsing.

---

### Phase 6: Frontend UI

**File**: `frontend/public/js/session.js`

**Form Injection**: 
- Target: Insert before `#questions-feed` element
- Method: `document.getElementById('questions-feed').insertAdjacentHTML('beforebegin', formHTML)`
- Why: No HTML changes needed, form dynamically rendered

**Form Components**:
- Textarea (280 char max)
- Character counter with color thresholds:
  - Default: #6b7280 (gray) when remaining > 80
  - Warning: #f59e0b (orange) when remaining ≤ 80
  - Danger: #dc2626 (red) when remaining ≤ 20
- Submit button with loading state (disabled during submission)
- Client-side validation (empty, too long, whitespace-only)
- Success: Clear form, reload question feed via `await loadQuestions()`, scroll to top
- Error handling: Map backend errors to user-friendly messages, preserve form content

**Key Implementation Notes**:
- Counter updates on `input` event
- Submit button disabled when invalid or submitting
- No helper function needed: inline `await loadQuestions()` after success
- Form state preserved on error (don't clear textarea)

**Tests**: Manual - rendering, counter colors, validation, submission flow, error display.

---

###Phase 7: Frontend Styling

**File**: `frontend/public/css/styles.css`

**Styles to Add**:
- `.question-form` - Form container layout
- `.question-form textarea` - Input styling
- `.char-counter` - Counter base styles
- `.char-counter.warning` - Orange state (#f59e0b)
- `.char-counter.danger` - Red state (#dc2626)
- `.question-form button` - Primary button
- `.question-form button:hover` - Hover state
- `.question-form button:disabled` - Disabled/loading state
- `.question-form .error-message` - Error display styling

**Color Strategy**:
- Use existing hex codes directly (matches codebase convention)
- Add TODO comment: "TODO: Extract colors to CSS custom properties in styling refactor"
- Grep-able for future refactoring

**Key Colors**:
- Primary: #2563eb (blue)
- Danger: #dc2626 (red)
- Warning: #f59e0b (orange)
- Gray: #6b7280 (neutral text)

---

## Testing Strategy

Comprehensive test coverage across three layers (29 tests total):

**Repository Layer** (6 tests):
- create_question success with author
- anonymous mode with NULL author_user_id  
- field validation and schema compliance
- 280-char boundary testing
- unicode/emoji handling
- transaction rollback scenarios

**Service Layer** (11 tests):  
- submit_question success cases (with author, anonymous)
- SessionNotFoundError for invalid code
- NotParticipantError for non-participant user
- validation failures (empty body, too long, whitespace only)
- schema compliance and field population
- status defaults to 'pending'
- get_user_by_id integration

**API Layer** (12 tests):
- POST /sessions/{code}/questions success returns 201
- anonymous submission returns 201  
- missing X-User-Id header returns 400
- session not found returns 404
- user not participant returns 403
- validation errors return 422 (empty, too long, missing field)
- response structure matches QuestionSummary schema
- question appears in subsequent GET requests
- idempotency considerations

**Repository Tests** (`backend/tests/repositories/test_questions.py`):
```python
def test_create_question_success()
def test_create_question_anonymous()
def test_create_question_returns_complete_object()
def test_create_question_280_char_boundary()
def test_create_question_unicode_handling()
def test_create_question_transaction_rollback()
```

**Service Tests** (`backend/tests/services/test_sessions_service.py` - extend SessionService):
```python
def test_submit_question_success_with_author()
def test_submit_question_success_anonymous()
def test_submit_question_session_not_found()
def test_submit_question_user_not_found()
def test_submit_question_not_participant()
def test_submit_question_body_empty()
def test_submit_question_body_too_long()
def test_submit_question_body_whitespace_only()
def test_submit_question_returns_summary_schema()
def test_submit_question_status_defaults_pending()
def test_submit_question_body_trimming()
```

**API Tests** (`backend/tests/api/test_sessions.py` - extend):
```python
def test_post_question_success_201()
def test_post_question_anonymous_201()
def test_post_question_missing_x_user_id_header()
def test_post_question_session_not_found_404()
def test_post_question_user_not_participant_403()
def test_post_question_body_too_long_422()
def test_post_question_body_empty_422()
def test_post_question_invalid_json_422()
def test_post_question_returns_question_summary_schema()
def test_post_question_appears_in_feed()
def test_post_question_rate_limiting()
def test_post_question_concurrent_submissions()
```

---

## Success Criteria

- Questions can be submitted with display name attribution
- 280 character limit enforced on client and server
- Character counter shows orange at 200, red at 260
- Validation errors display clearly without losing typed content
- Question appears in feed immediately after submission
- Form clears and scrolls to new question on success
- 84 existing tests remain passing
- 29 new tests passing (6 repository + 11 service + 12 API)
- API follows RESTful conventions with proper HTTP status codes
- No XSS vulnerabilities (all user input escaped)
- User ID properly stored and retrieved from sessionStorage

---

## Implementation Sequence

1. **User ID tracking (non-breaking)**:
   - Backend: Add X-Created-User-Id header to join/create endpoints (api/routes/sessions.py)
   - Frontend: Extract header in api.js, augment sessionStorage in ui.js
   - Verify: sessionStorage contains `{...session, userId}`, existing tests pass
   
2. **Repository layer**:
   - Implement create_question() with author_user_id support
   - Implement count_user_pending_questions() for limit enforcement
   - Add 6 tests (success, anonymous, validation, boundaries, unicode, rollback)
   
3. **Service layer**:
   - Extend SessionService with submit_question()
   - Add exceptions: NotParticipantError, QuestionLimitExceededError, InvalidQuestionBodyError
   - Add race condition TODO comment in count logic
   - Separate get_participant() and get_user_by_id() calls
   - Add 11 tests (success, errors, validation, schemas)
   
4. **API layer**:
   - Add POST /sessions/{code}/questions with X-User-Id header validation
   - Response: 201 QuestionSummary | 422/403/404 errors
   - Add 12 tests (success, errors, integration with feed)
   
5. **Frontend API**:
   - Implement submitQuestion(code, body, userId) in api.js
   - Set X-User-Id header from parameter
   
6. **Frontend UI**:
   - Inject form before #questions-feed using insertAdjacentHTML
   - Character counter with 3 color states (gray/orange/red)
   - Client validation, submit handler
   - Success: clear form, await loadQuestions(), scroll top
   - Error: preserve content, show message
   
7. **Styling**:
   - Add form/textarea/counter/button/error styles
   - Use hex codes (#2563eb, #dc2626, #f59e0b, #6b7280)
   - Add TODO comment for future CSS variable refactor
   
8. **Integration testing**:
   - End-to-end flow: join → submit → verify in feed
   - Error scenarios: not participant, limit exceeded, validation
   
9. **Documentation**:
   - Update API docs (sessions.md) with POST endpoint
   - Update frontend guide with form component
   - Update agent.md with architectural decisions
   
10. **Verification**:
    - All 84 existing tests pass
    - All 29 new tests pass (6 + 11 + 12)
    - Manual testing: character counter colors, error handling, success flow

**Key Principle**: Non-breaking changes first (header approach), accept MVP limitations with clear documentation (race condition), match existing patterns (hex codes, sessionStorage augmentation).

Estimated completion: 2-3 days (with comprehensive test coverage)

---

## Error Handling Reference

| Error | HTTP | Message |
|-------|------|---------|
| Missing X-User-Id | 422 | "X-User-Id header required" |
| Session not found | 404 | "Session not found" |
| Not participant | 403 | "Must join session before asking questions" |
| Body empty | 422 | "Question body cannot be empty" |
| Body too long | 422 | "Question exceeds 280 characters" |
| Body whitespace only | 422 | "Question body cannot be empty" |

**Note**: FastAPI automatically returns 422 for missing required parameters and validation errors, not 400.

---

## Data Flow Summary

```
User types question → Character counter updates → Submit clicked
  ↓
Validate locally (length, non-empty) → Show errors if invalid
  ↓
GET userId from sessionStorage.currentSession.userId
  ↓
POST /sessions/{code}/questions + X-User-Id header + QuestionCreate body
  ↓
API validates: session exists, user is participant, X-User-Id header present
  ↓
Service layer:
  - Look up session by code
  - Verify user is participant
  - Get user display_name via separate get_user_by_id() call
  - Count pending questions (NOTE: race condition possible due to autocommit)
  - Validate count < 3
  - Create question record
  ↓
Repository creates question → Returns dict
  ↓
Service builds QuestionSummary with author details → Returns to API
  ↓
API returns 201 + QuestionSummary
  ↓
Frontend receives response → Clears form → Calls await loadQuestions() → Scrolls to top
```

**Key Technical Notes**:
- sessionStorage structure: `{...session, userId}` (augmented, not replaced)
- User ID transmitted via X-User-Id request header
- User ID received via X-Created-User-Id response header (join/create)
- Race condition acknowledged in count validation (fixed in future transaction refactor)
- No helper function: direct call to existing `loadQuestions()`
- Form injected dynamically before question feed (no HTML changes)

---

## Implementation Outcomes

**Status**: Ready for implementation
**Expected Completion**: 2-3 days with full test coverage
**Test Count Target**: 29 tests (6 repository + 11 service + 12 API)

### Refactoring Decisions (October 21, 2025)

After external review identified 7 critical issues, the plan was refactored with focus on **maintainability** and **upgradeability**:

**1. User ID Tracking** (Breaking → Non-Breaking):
- **Original**: Modify join_session() return type to tuple, breaking 10+ files
- **Refactored**: Use X-Created-User-Id response header
- **Impact**: Zero breaking changes, backwards compatible, clean upgrade path

**2. Race Condition** (Blocking → Documented Limitation):
- **Original**: Blocked on transaction implementation
- **Refactored**: Accept MVP limitation, document with TODO for future fix
- **Rationale**: Removing autocommit requires auditing 84 tests, risk > benefit for soft limit
- **Mitigation**: Client-side button disabling, clear documentation

**3. sessionStorage Structure** (Replace → Augment):
- **Original**: Replace sessionStorage with new structure
- **Refactored**: Augment existing session object with userId
- **Impact**: Zero breaking changes, single source of truth

**4. CSS Styling** (New Variables → Use Existing):
- **Original**: Plan referenced non-existent CSS variables
- **Refactored**: Use existing hex codes, add TODO for future refactor
- **Rationale**: Matches codebase patterns, feature delivery > architecture perfection

**5. Form Placement** (HTML Modification → Dynamic Injection):
- **Original**: Assumed question-form-container div exists
- **Refactored**: Inject form dynamically before question feed
- **Impact**: No HTML changes, form logic colocated with behavior

**6. Helper Function** (New Abstraction → Inline):
- **Original**: Create refreshQuestionFeed() helper
- **Refactored**: Inline await loadQuestions() at single call site
- **Rationale**: YAGNI principle, avoid premature abstraction

**7. Error Codes** (Factual Correction):
- **Original**: Listed 400 for missing header
- **Refactored**: Corrected to 422 (FastAPI validation behavior)

**Guiding Principles**:
- Prioritise non-breaking changes over "perfect" architecture
- Accept documented limitations over risky infrastructure changes
- Match existing codebase patterns for consistency
- Defer architectural improvements to dedicated refactor sprints
- Truth over assumptions (verify FastAPI behavior, actual response codes)

This section will be updated with implementation details, statistics, and learnings after completion.

````

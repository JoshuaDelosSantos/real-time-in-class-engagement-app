# Session Details Backend — Planning & Implementation Log

## Goal

Implement three GET endpoints to retrieve session details, participant roster, and question lists, enabling the frontend to display meaningful content on the session page.

## Context

**Current State**:
- Session creation and joining work end-to-end
- `SessionSummary` only exposes basic fields (id, code, title, status, host, created_at)
- Session page UI cannot display participant lists or questions
- Schemas exist but no API endpoints expose the data

**Why This Matters**:
Without these endpoints, the session page would only show the same information already visible in the join success message. Building frontend UI first would result in empty states and placeholders with no real data to display.

## Gap Analysis

### What Exists Today

1. **Database Schema** ✓
   - `session_participants` table with user FK and role
   - `questions` table with session FK, author FK, status, likes
   - Proper indexes and constraints

2. **Repository Layer** ⚠️ (Partial)
   - `get_session_by_code()` exists but only used internally
   - `add_participant()` and `get_participant()` exist
   - Need: `list_session_participants()`
   - Need: `list_session_questions()`

3. **Schemas** ✓ (Complete but Unused)
   - `SessionParticipantSummary` with user, role, joined_at fields
   - `QuestionSummary` with id, session_id, body, status, likes, author, created_at
   - `UserSummary` for embedding user details

4. **Service Layer** ✗
   - No `get_session_details()` method
   - No `get_session_participants()` method
   - No `get_session_questions()` method

5. **API Endpoints** ✗
   - No `GET /sessions/{code}` route
   - No `GET /sessions/{code}/participants` route
   - No `GET /sessions/{code}/questions` route

### What's Missing

1. **Repository Functions**
   - `list_session_participants(session_id)` → List of participant records with user data
   - `list_session_questions(session_id)` → List of questions with author data (nullable)
   - Update `backend/app/repositories/__init__.py` to expose new functions

2. **Service Layer**
   - `get_session_details(code)` → Returns session with enriched host data
   - `get_session_participants(code)` → Returns participant list with user summaries
   - `get_session_questions(code)` → Returns question list with optional author summaries

3. **API Routes**
   - `GET /sessions/{code}` → Single session retrieval
   - `GET /sessions/{code}/participants` → Participant roster
   - `GET /sessions/{code}/questions` → Question feed with status filtering

4. **Testing**
   - Repository tests for new list functions (including NULL author handling)
   - Service tests for enrichment logic
   - API integration tests for all three endpoints

5. **Documentation**
   - API endpoint docs in `docs/api/sessions.md`
   - Update backend README

## Implementation Plan

### Phase 1: GET /sessions/{code} — Single Session Retrieval

**Repository Layer** (`backend/app/repositories/sessions.py`):
- Expose existing `get_session_by_code()` (currently used internally)
- No changes needed — function already returns full session record

**Service Layer** (`backend/app/services/sessions.py`):
- Add `get_session_details(code: str) -> SessionSummary`
- Responsibilities:
  - Look up session by code
  - Raise `SessionNotFoundError` if not found
  - Fetch host user record
  - Return `SessionSummary` with embedded `UserSummary`

**API Layer** (`backend/app/api/routes/sessions.py`):
- Add endpoint: `GET /sessions/{code}`
- Path param: `code` (string)
- Response: `SessionSummary` (200) or 404 if not found
- Error handling: Map `SessionNotFoundError` to HTTP 404

**Testing**:
- Service test: successful retrieval with host data
- Service test: raises error for non-existent code
- API test: 200 response with complete session data
- API test: 404 response for invalid code
- API test: verify response structure matches schema

### Phase 2: GET /sessions/{code}/participants — Participant Roster

**Repository Layer** (`backend/app/repositories/session_participants.py`):
- Add `list_session_participants(session_id: int) -> list[dict]`
- Query joins `session_participants` with `users` table
- Return list of dicts with: user_id, display_name, role, joined_at
- Order by: role DESC (host first), joined_at ASC (earliest first)

**Service Layer** (`backend/app/services/sessions.py`):
- Add `get_session_participants(code: str) -> list[SessionParticipantSummary]`
- Responsibilities:
  - Look up session by code
  - Raise `SessionNotFoundError` if not found
  - Call repository to fetch participant records
  - Map to `SessionParticipantSummary` schema
  - Return list with embedded `UserSummary` objects

**API Layer** (`backend/app/api/routes/sessions.py`):
- Add endpoint: `GET /sessions/{code}/participants`
- Path param: `code` (string)
- Response: `list[SessionParticipantSummary]` (200) or 404 if session not found
- Empty list is valid response (no participants yet)
- Error handling: Map `SessionNotFoundError` to HTTP 404

**Testing**:
- Repository test: empty list for session with no participants
- Repository test: multiple participants ordered correctly
- Repository test: host appears first in list
- Service test: enriches with user summaries
- API test: 200 response with participant array
- API test: 404 for invalid session code
- API test: empty array for new session
- API test: verify ordering (host first, then by join time)

### Phase 3: GET /sessions/{code}/questions — Question Feed

**Repository Layer** (`backend/app/repositories/questions.py` — new file):
- Add `list_session_questions(session_id: int, status_filter: str | None = None) -> list[dict]`
- Query joins `questions` with `users` table for author details (LEFT JOIN since `author_user_id` is nullable)
- Return list of dicts with: id, session_id, body, status, likes, author_id, author_display_name, created_at
- Author fields can be NULL for anonymous questions
- Order by: created_at DESC (newest first)
- If `status_filter` provided, filter by question status ("pending" or "answered")
- Expose via `backend/app/repositories/__init__.py` for service layer access

**Service Layer** (`backend/app/services/sessions.py`):
- Add `get_session_questions(code: str, status: str | None = None) -> list[QuestionSummary]`
- Responsibilities:
  - Look up session by code
  - Raise `SessionNotFoundError` if not found
  - Call repository to fetch question records
  - Map to `QuestionSummary` schema with embedded author `UserSummary` (or None for anonymous questions)
  - Handle NULL author_id gracefully
  - Return list of questions

**API Layer** (`backend/app/api/routes/sessions.py`):
- Add endpoint: `GET /sessions/{code}/questions`
- Path param: `code` (string)
- Query param: `status` (optional, values: "pending", "answered")
- Response: `list[QuestionSummary]` (200) or 404 if session not found
- Empty list is valid response (no questions yet)
- Error handling: Map `SessionNotFoundError` to HTTP 404

**Testing**:
- Repository test: empty list for session with no questions
- Repository test: multiple questions ordered by created_at DESC
- Repository test: status filter works correctly ("pending" vs "answered")
- Repository test: author details included when present
- Repository test: NULL author_id handled correctly (anonymous questions)
- Service test: enriches with author user summaries
- Service test: handles questions with NULL authors (maps to None)
- Service test: handles sessions with no questions
- API test: 200 response with question array
- API test: 404 for invalid session code
- API test: empty array for new session
- API test: status query parameter filtering ("pending", "answered")
- API test: verify ordering (newest first)
- API test: verify author data embedded (or None for anonymous)

## Error Handling

**Shared Exception**:
- `SessionNotFoundError` — reuse existing exception from join flow

**HTTP Status Mapping**:
- `SessionNotFoundError` → 404 Not Found
- Any other exception → 500 Internal Server Error

**Consistent Responses**:
All three endpoints follow the same pattern:
- Session not found → 404 with error detail
- Success → 200 with data (possibly empty list)
- No 422 validation errors (path params are strings)

## Data Model Alignment

All schemas already exist and tested:

**SessionSummary**:
```python
id: int
code: str
title: str
status: str
host: UserSummary
created_at: datetime
```

**SessionParticipantSummary**:
```python
user: UserSummary
role: str
joined_at: datetime
```

**QuestionSummary**:
```python
id: int
session_id: int
body: str
status: str
likes: int
author: UserSummary
created_at: datetime
```

**UserSummary**:
```python
id: int
display_name: str
```

## Implementation Order

1. **GET /sessions/{code}** — simplest, reuses existing repository function
2. **GET /sessions/{code}/participants** — builds on session lookup pattern
3. **GET /sessions/{code}/questions** — most complex, new repository file needed

Each phase follows: Repository → Service → API → Tests → Documentation

## Testing Strategy

**Repository Tests**:
- Focus on query correctness, joins, ordering, filtering
- Test empty results and multi-row results
- Verify FK relationships work correctly

**Service Tests**:
- Focus on orchestration and data enrichment
- Mock repository calls
- Test error handling (session not found)
- Verify schema mapping

**API Tests**:
- Integration tests using test database
- Test happy paths and error cases
- Verify HTTP status codes
- Validate response structure against schemas

**Coverage Goals**:
- All new repository functions: 100%
- All new service methods: 100%
- All new API endpoints: success + error cases

## Documentation Updates

**Backend README** (`backend/app/README.md`):
- Add "Session Details Endpoints" section
- Document all three GET routes with parameters

**API Docs** (`docs/api/sessions.md`):
- Add GET /sessions/{code} endpoint
- Add GET /sessions/{code}/participants endpoint
- Add GET /sessions/{code}/questions endpoint
- Include request/response examples
- Document query parameters

**Root README**:
- Update "Current Capabilities" section
- List new endpoints in features

## Success Criteria

- [ ] All three GET endpoints implemented and working
- [ ] Repository functions tested with 100% coverage
- [ ] Service methods tested with 100% coverage
- [ ] API endpoints tested with success and error cases
- [ ] All tests passing in CI
- [ ] Documentation updated
- [ ] Frontend can fetch session details, participants, and questions
- [ ] Session page UI unblocked for meaningful implementation

## Risks & Follow-ups

**Risks**:
- Query performance with large participant lists (mitigated by proper indexes)
- Question feed ordering may need pagination in future
- Anonymous questions (NULL author_id) must be handled throughout the stack

**Follow-ups**:
- Phase 8: Build session page UI using these endpoints
- Phase 9: Question submission (POST /sessions/{code}/questions)
- Future: Real-time updates via WebSocket for live data
- Future: Pagination for questions endpoint if needed
- Future: Filtering/sorting options for participants
- Future: Consider additional question statuses if needed (would require migration)

## Outcome

(To be filled in after implementation)

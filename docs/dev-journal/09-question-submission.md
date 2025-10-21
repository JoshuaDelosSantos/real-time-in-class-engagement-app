# Question Submission — Planning & Implementation Log

## Goal

Implement complete question submission feature allowing participants to submit questions during live sessions, with backend validation, storage, and frontend UI for submission and display.

## Context

**Current State**:
- Session creation, joining, and detail viewing work end-to-end
- Session page displays participant roster and question feed (read-only)
- Question database schema exists with all constraints and indexes
- `QuestionCreate` schema exists for submission validation
- `list_session_questions()` repository function exists for retrieval
- No endpoint or UI for submitting questions

**Why This Matters**:
Questions are the core interaction in ClassEngage. Without submission capability, the session page is a static view with no participant engagement. This feature unlocks the primary use case: students asking questions during class and seeing them appear in real-time.

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

### Phase 1: Repository Layer — Question Creation

**File**: `backend/app/repositories/questions.py`

Add two new functions:

```python
def create_question(
    conn: psycopg.Connection,
    session_id: int,
    author_user_id: int | None,
    body: str,
) -> dict:
    """Create a new question in a session.
    
    Returns the complete question record including generated fields.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO questions (session_id, author_user_id, body)
            VALUES (%s, %s, %s)
            RETURNING id, session_id, author_user_id, body, status, likes, created_at, answered_at
            """,
            (session_id, author_user_id, body),
        )
        result = cur.fetchone()
        if result is None:
            raise RuntimeError("Failed to create question")
        return result


def count_user_pending_questions(
    conn: psycopg.Connection,
    session_id: int,
    user_id: int,
) -> int:
    """Count pending questions submitted by a user in a session.
    
    Used to enforce the 3-question limit per user per session.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM questions
            WHERE session_id = %s 
              AND author_user_id = %s 
              AND status = 'pending'
            """,
            (session_id, user_id),
        )
        result = cur.fetchone()
        return result[0] if result else 0
```

**Update Exports**: Add both functions to `backend/app/repositories/__init__.py`

### Phase 2: Service Layer — Question Submission Logic

**Decision**: Create new file `backend/app/services/questions.py` to separate question logic from session logic (follows separation of concerns).

**File**: `backend/app/services/questions.py`

```python
"""Service layer for question submission and management."""

from __future__ import annotations

from app.db import get_connection
from app.repositories import (
    count_user_pending_questions,
    create_question,
    get_participant,
    get_session_by_code,
)
from app.schemas import QuestionSummary, UserSummary


class SessionNotFoundError(RuntimeError):
    """Raised when a session code doesn't match any session."""


class SessionNotActiveError(RuntimeError):
    """Raised when attempting to submit to a non-active session."""


class NotParticipantError(RuntimeError):
    """Raised when a user tries to submit without being a participant."""


class QuestionLimitExceededError(RuntimeError):
    """Raised when a user exceeds the 3 pending questions limit."""


class InvalidQuestionBodyError(RuntimeError):
    """Raised when question body fails validation."""


class QuestionService:
    """Orchestrates question submission and management operations."""

    def submit_question(
        self,
        session_code: str,
        user_id: int,
        body: str,
    ) -> QuestionSummary:
        """Submit a new question to a session.
        
        Args:
            session_code: The session join code
            user_id: ID of the user submitting the question
            body: Question text (1-280 characters)
            
        Returns:
            QuestionSummary with the created question
            
        Raises:
            SessionNotFoundError: Session doesn't exist
            SessionNotActiveError: Session is not in 'active' status
            NotParticipantError: User is not a participant in the session
            QuestionLimitExceededError: User has 3 pending questions already
            InvalidQuestionBodyError: Body is empty or whitespace-only
        """
        # Validate question body
        trimmed_body = body.strip()
        if not trimmed_body:
            raise InvalidQuestionBodyError("Question body cannot be empty")
        
        with get_connection() as conn:
            # Look up session
            session = get_session_by_code(conn, session_code)
            if not session:
                raise SessionNotFoundError("Session not found")
            
            # Validate session is active
            if session["status"] != "active":
                raise SessionNotActiveError(
                    "Questions can only be submitted to active sessions"
                )
            
            # Validate user is a participant
            participant = get_participant(conn, session["id"], user_id)
            if not participant:
                raise NotParticipantError(
                    "Only session participants can submit questions"
                )
            
            # Enforce 3-question limit
            pending_count = count_user_pending_questions(
                conn, session["id"], user_id
            )
            if pending_count >= 3:
                raise QuestionLimitExceededError(
                    "You have reached the maximum of 3 pending questions"
                )
            
            # Create question
            question = create_question(
                conn,
                session_id=session["id"],
                author_user_id=user_id,
                body=trimmed_body,
            )
            
            conn.commit()
            
            # Build response with author summary
            author_summary = UserSummary(
                id=user_id,
                display_name=participant["user_display_name"],
            )
            
            return QuestionSummary(
                id=question["id"],
                session_id=question["session_id"],
                body=question["body"],
                status=question["status"],
                likes=question["likes"],
                author=author_summary,
                created_at=question["created_at"],
            )
```

**Update Exports**: Add `QuestionService` to `backend/app/services/__init__.py`

### Phase 3: API Endpoint — Question Submission

**File**: `backend/app/api/routes/sessions.py`

Add new endpoint after existing routes:

```python
@router.post(
    "/{code}/questions",
    response_model=QuestionSummary,
    status_code=status.HTTP_201_CREATED,
)
def submit_question(
    code: str,
    payload: QuestionCreate,
    user_id: int = Header(..., alias="X-User-Id"),
    service: QuestionService = Depends(lambda: QuestionService()),
) -> QuestionSummary:
    """Submit a new question to a session.
    
    Participants can submit questions to active sessions. Each user
    is limited to 3 pending questions per session.
    
    Args:
        code: Session join code (path parameter)
        payload: Question data with body field
        user_id: User ID from X-User-Id header
        service: Question service dependency
        
    Returns:
        QuestionSummary: The created question with author details
        
    Raises:
        HTTPException:
            - 400: Invalid question body (empty/whitespace)
            - 403: User not a participant or limit exceeded
            - 404: Session not found
            - 409: Session not active (draft or ended)
    """
    from app.services.questions import (
        InvalidQuestionBodyError,
        NotParticipantError,
        QuestionLimitExceededError,
        SessionNotActiveError,
        SessionNotFoundError,
    )
    
    try:
        return service.submit_question(code, user_id, payload.body)
    except InvalidQuestionBodyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (NotParticipantError, QuestionLimitExceededError) as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SessionNotActiveError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
```

**Import Updates**: Add `Header` from `fastapi` and `QuestionCreate`, `QuestionSummary` from schemas

### Phase 4: Frontend API Function — Question Submission

**File**: `frontend/public/js/api.js`

Add new function after existing functions:

```javascript
/**
 * Submit a new question to a session.
 * 
 * @param {string} code - The 6-character session join code
 * @param {string} body - Question text (1-280 characters)
 * @param {number} userId - ID of the user submitting the question
 * @returns {Promise<Object>} Created question object
 * @throws {Error} If the request fails or returns non-2xx status
 */
async function submitQuestion(code, body, userId) {
  const response = await fetch(`${API_BASE_URL}/sessions/${code}/questions`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'X-User-Id': userId.toString()
    },
    body: JSON.stringify({ body: body })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let message = `HTTP ${response.status}`;
    
    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        message = errorData.detail[0]?.msg || JSON.stringify(errorData.detail);
      } else {
        message = errorData.detail;
      }
    }
    
    throw new Error(message);
  }
  
  return await response.json();
}
```

### Phase 5: Frontend UI — Question Submission Form

**File**: `frontend/public/js/session.js`

Add form rendering and event handling:

```javascript
/**
 * Render question submission form
 */
function renderQuestionForm() {
  const formContainer = document.getElementById('question-form-container');
  if (!formContainer) return;
  
  // Get user ID from sessionStorage
  const sessionData = sessionStorage.getItem('currentSession');
  if (!sessionData) {
    formContainer.innerHTML = `
      <div class="info-message">
        <p>Please join the session to submit questions.</p>
      </div>
    `;
    return;
  }
  
  const session = JSON.parse(sessionData);
  
  formContainer.innerHTML = `
    <form id="question-form" class="question-form">
      <div class="form-group">
        <label for="question-body">Ask a Question</label>
        <textarea 
          id="question-body" 
          placeholder="What would you like to ask?" 
          maxlength="280"
          rows="3"
          required
        ></textarea>
        <div class="char-counter">
          <span id="char-count">0</span> / 280 characters
        </div>
      </div>
      <button type="submit" id="submit-question-btn" class="button">
        Submit Question
      </button>
      <div id="question-form-output"></div>
    </form>
  `;
  
  setupQuestionFormHandlers();
}

/**
 * Set up question form event handlers
 */
function setupQuestionFormHandlers() {
  const form = document.getElementById('question-form');
  const textarea = document.getElementById('question-body');
  const charCount = document.getElementById('char-count');
  const submitButton = document.getElementById('submit-question-btn');
  const output = document.getElementById('question-form-output');
  
  if (!form || !textarea || !charCount || !submitButton || !output) {
    console.warn('Question form elements not found');
    return;
  }
  
  // Character counter
  textarea.addEventListener('input', () => {
    const length = textarea.value.length;
    charCount.textContent = length;
    
    // Visual feedback for character limit
    if (length > 260) {
      charCount.style.color = '#dc2626'; // Red warning
    } else if (length > 200) {
      charCount.style.color = '#f59e0b'; // Orange caution
    } else {
      charCount.style.color = '#64748b'; // Default gray
    }
  });
  
  // Form submission
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const body = textarea.value.trim();
    
    // Client-side validation
    if (!body) {
      renderQuestionFormError(output, 'Please enter a question');
      return;
    }
    
    if (body.length > 280) {
      renderQuestionFormError(output, 'Question must be 280 characters or less');
      return;
    }
    
    // Get user ID from sessionStorage
    const sessionData = sessionStorage.getItem('currentSession');
    if (!sessionData) {
      renderQuestionFormError(output, 'Session data not found. Please rejoin the session.');
      return;
    }
    
    const session = JSON.parse(sessionData);
    if (!session.userId) {
      renderQuestionFormError(output, 'User ID not found. Please rejoin the session.');
      return;
    }
    
    // Disable during request
    submitButton.disabled = true;
    textarea.disabled = true;
    output.innerHTML = '<div class="loading-message">Submitting question...</div>';
    
    try {
      const question = await submitQuestion(
        currentSessionCode,
        body,
        session.userId
      );
      
      renderQuestionFormSuccess(output);
      form.reset();
      charCount.textContent = '0';
      charCount.style.color = '#64748b';
      
      // Refresh question feed to show new question
      await refreshQuestionFeed();
      
    } catch (error) {
      renderQuestionFormError(output, error.message);
    } finally {
      submitButton.disabled = false;
      textarea.disabled = false;
    }
  });
}

/**
 * Render question form success message
 */
function renderQuestionFormSuccess(element) {
  element.innerHTML = `
    <div class="success-message">
      <p>✓ Question submitted successfully!</p>
    </div>
  `;
  
  // Clear success message after 3 seconds
  setTimeout(() => {
    element.innerHTML = '';
  }, 3000);
}

/**
 * Render question form error message
 */
function renderQuestionFormError(element, errorMessage) {
  const friendlyMessages = {
    'Session not found': 'Session not found. Please check the session code.',
    'Questions can only be submitted to active sessions': 'This session is not active. Questions cannot be submitted.',
    'Only session participants can submit questions': 'You must join the session before submitting questions.',
    'You have reached the maximum of 3 pending questions': 'You have 3 pending questions. Wait for them to be answered before submitting more.',
    'Question body cannot be empty': 'Please enter a question before submitting.',
  };
  
  const displayMessage = friendlyMessages[errorMessage] || errorMessage;
  
  element.innerHTML = `
    <div class="error-message">
      <p>${escapeHtml(displayMessage)}</p>
    </div>
  `;
}

/**
 * Refresh question feed after submission
 */
async function refreshQuestionFeed() {
  const feedElement = document.getElementById('questions-feed');
  if (!feedElement) return;
  
  try {
    const questions = await getSessionQuestions(currentSessionCode, currentFilter);
    renderQuestionFeed(questions);
  } catch (error) {
    console.error('Failed to refresh question feed:', error);
  }
}
```

**Update HTML**: Add form container to `session.html`:

```html
<!-- Question Submission Form (add before questions section) -->
<section>
  <h2>Submit a Question</h2>
  <div id="question-form-container">
    <div class="loading-message">Loading form...</div>
  </div>
</section>
```

**Update `initializeSessionPage()`**: Call `renderQuestionForm()` after loading session data:

```javascript
async function initializeSessionPage() {
  const urlParams = new URLSearchParams(window.location.search);
  currentSessionCode = urlParams.get('code');
  
  if (!currentSessionCode) {
    window.location.href = '/';
    return;
  }
  
  setupQuestionFilters();
  await loadSessionData();
  renderQuestionForm(); // Add this line
}
```

### Phase 6: CSS Styling — Question Form

**File**: `frontend/public/css/styles.css`

Add styles for question form:

```css
/* ============================================================
   Question Submission Form
   ============================================================ */

.question-form {
  background: #fff;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.question-form textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.375rem;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

.question-form textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.char-counter {
  margin-top: 0.25rem;
  text-align: right;
  font-size: 0.875rem;
  color: #64748b;
}

.info-message {
  background: #f0f9ff;
  border-left: 4px solid #2563eb;
  padding: 1rem;
  border-radius: 0.375rem;
  color: #1e40af;
}
```

### Phase 7: User Context Management

**Critical Decision**: How do we track user identity across page navigation?

**Solution**: Store user ID in sessionStorage when joining/creating session

**Update Join Success Handler** (`frontend/public/js/ui.js`):

```javascript
// In renderJoinSuccess(), update sessionStorage:
sessionStorage.setItem('currentSession', JSON.stringify({
  code: session.code,
  title: session.title,
  userId: userId, // Add this line
  displayName: displayName,
  joinedAt: new Date().toISOString()
}));
```

**Update Create Success Handler** (`frontend/public/js/ui.js`):

```javascript
// In renderCreateSuccess(), update sessionStorage:
sessionStorage.setItem('currentSession', JSON.stringify({
  code: session.code,
  title: session.title,
  userId: session.host.id, // Add this line
  displayName: session.host.display_name,
  isHost: true,
  createdAt: new Date().toISOString()
}));
```

**Note**: User ID comes from the API response. Need to verify backend returns user ID in join/create responses.

### Phase 8: Testing Strategy

**Repository Tests** (`backend/tests/repositories/test_questions.py`):
- Test `create_question()` with valid data
- Test `create_question()` returns all fields
- Test `create_question()` with NULL author_user_id (anonymous)
- Test `count_user_pending_questions()` returns 0 for no questions
- Test `count_user_pending_questions()` counts only pending questions
- Test `count_user_pending_questions()` filters by session and user
- Test `count_user_pending_questions()` excludes answered questions

**Service Tests** (`backend/tests/services/test_questions_service.py` - new file):
- Test successful question submission
- Test `SessionNotFoundError` for invalid code
- Test `SessionNotActiveError` for draft session
- Test `SessionNotActiveError` for ended session
- Test `NotParticipantError` for non-participant user
- Test `QuestionLimitExceededError` when user has 3 pending questions
- Test `InvalidQuestionBodyError` for empty body
- Test `InvalidQuestionBodyError` for whitespace-only body
- Test body trimming (leading/trailing whitespace removed)
- Test response includes author summary
- Test response includes all question fields

**API Tests** (`backend/tests/api/test_sessions.py` - extend):
- Test 201 response with valid question submission
- Test 400 for empty body
- Test 403 for non-participant
- Test 403 for exceeding question limit
- Test 404 for invalid session code
- Test 409 for inactive session
- Test 422 for missing body field (Pydantic validation)
- Test 422 for body exceeding 280 characters
- Test response structure matches `QuestionSummary` schema
- Test question appears in subsequent GET requests

**Frontend Testing** (Manual):
- Submit question as participant → appears in feed
- Submit question with 280 characters → succeeds
- Submit question with 281 characters → client-side error
- Submit empty question → client-side error
- Submit 3 questions → 4th submission shows limit error
- Submit to ended session → shows session not active error
- Submit without joining → shows not participant error
- Character counter updates correctly
- Character counter shows warning colors
- Success message displays and auto-clears
- Question feed refreshes after submission

## Key Decisions

### 1. Service Module Separation
**Decision**: Create `backend/app/services/questions.py` separate from `sessions.py`  
**Rationale**: Questions have distinct business logic (limits, status validation) that would clutter the session service. Follows single responsibility principle and makes codebase more maintainable as question features grow (voting, moderation, etc.).

### 2. User Identity via Header
**Decision**: Pass user ID via `X-User-Id` header instead of session/cookie/JWT  
**Rationale**: MVP approach matching "no authentication" requirement. Simple to implement, works with current architecture. Frontend gets user ID from sessionStorage. Future: replace with proper authentication tokens.

### 3. Session Status Validation
**Decision**: Only allow questions in "active" sessions, not "draft" or "ended"  
**Rationale**: Draft sessions are pre-start setup; ended sessions are archived. Questions only make sense during active classroom time. Returns 409 Conflict to distinguish from 404 (session not found).

### 4. Question Limit Enforcement
**Decision**: Enforce 3 pending questions per user per session at service layer  
**Rationale**: Keeps queue manageable, prevents spam. Counting happens at submission time (not via database constraint) to provide clear error message. Limit resets when questions are answered.

### 5. Character Counter UX
**Decision**: Show real-time character count with color warnings at 200 and 260 chars  
**Rationale**: Provides progressive feedback. Users can self-regulate before hitting hard limit. Color coding (gray → orange → red) gives visual cue without blocking input.

### 6. Author Attribution
**Decision**: Always attribute questions (non-NULL author_user_id)  
**Rationale**: Accountability and context for hosts. Database supports NULL for future anonymous mode, but MVP requires participation which implies identity. Consistent with user context management.

### 7. Automatic Feed Refresh
**Decision**: Refresh question feed immediately after successful submission  
**Rationale**: Provides instant feedback that submission worked. User sees their question appear in the feed. Future: WebSocket will handle this automatically for all participants.

### 8. Body Trimming
**Decision**: Trim whitespace at service layer before storing  
**Rationale**: Prevents accidental whitespace-only submissions. Database stores clean data. Frontend shows exactly what was stored. Consistent with display name handling in user creation.

### 9. Error Message Mapping
**Decision**: Map technical errors to user-friendly messages in frontend  
**Rationale**: Backend returns precise technical messages; frontend translates for end users. Separation of concerns: backend focused on correctness, frontend on UX.

### 10. Form Placement
**Decision**: Place submission form above question feed  
**Rationale**: Call-to-action at top encourages participation. Users see form before scrolling through existing questions. Follows natural top-to-bottom flow.

## Success Criteria

- [ ] `create_question()` repository function implemented and tested
- [ ] `count_user_pending_questions()` repository function implemented and tested
- [ ] `QuestionService` class created with `submit_question()` method
- [ ] All service-layer exceptions defined and handled
- [ ] POST `/sessions/{code}/questions` endpoint working
- [ ] Frontend `submitQuestion()` API function implemented
- [ ] Question submission form renders on session page
- [ ] Character counter updates in real-time with color warnings
- [ ] Form validation prevents empty/oversized submissions
- [ ] Success feedback shows and auto-clears
- [ ] Question feed refreshes after successful submission
- [ ] User ID properly stored and retrieved from sessionStorage
- [ ] All repository tests passing (7+ tests)
- [ ] All service tests passing (10+ tests)
- [ ] All API tests passing (9+ tests)
- [ ] Manual frontend testing completed
- [ ] Error messages are user-friendly
- [ ] No XSS vulnerabilities (all user input escaped)
- [ ] Documentation updated

## Implementation Sequence

### Backend (Phases 1-3)
1. Repository layer: `create_question()` and `count_user_pending_questions()`
2. Repository tests (7 tests)
3. Service layer: `QuestionService` with `submit_question()`
4. Service tests (10 tests)
5. API endpoint: POST `/sessions/{code}/questions`
6. API tests (9 tests)
7. Verify all backend tests passing

### Frontend (Phases 4-7)
8. API function: `submitQuestion()`
9. User context: Update join/create handlers to store user ID
10. Session page: Render question form
11. Event handlers: Form submission, character counter, validation
12. CSS: Form styling and character counter
13. Integration: Form → API → Feed refresh
14. Manual testing all user flows

### Documentation (Phase 8)
15. Update API docs with POST endpoint
16. Update backend README
17. Record implementation outcomes in this file
18. Update root README capabilities

## Error Handling Matrix

| HTTP Code | Error Type | User Message |
|-----------|------------|--------------|
| 400 | Empty body | "Please enter a question before submitting." |
| 403 | Not participant | "You must join the session before submitting questions." |
| 403 | Question limit | "You have 3 pending questions. Wait for them to be answered before submitting more." |
| 404 | Session not found | "Session not found. Please check the session code." |
| 409 | Session not active | "This session is not active. Questions cannot be submitted." |
| 422 | Pydantic validation | Extract from error array |

## Data Flow

```
User types question
  ↓
Client-side validation (length, empty)
  ↓
submitQuestion(code, body, userId)
  ↓
POST /sessions/{code}/questions with X-User-Id header
  ↓
QuestionService.submit_question()
  ├─ Validate body (empty check)
  ├─ Look up session by code
  ├─ Validate session is active
  ├─ Validate user is participant
  ├─ Check pending question count
  ├─ Create question record
  └─ Return QuestionSummary
  ↓
201 response with question data
  ↓
Show success message
  ↓
Refresh question feed
  ↓
User sees their question in the feed
```

## Future Enhancements

- **Anonymous Questions**: Toggle for submitting without attribution (NULL author_user_id)
- **WebSocket Updates**: Real-time question feed updates for all participants
- **Question Editing**: Allow users to edit their pending questions
- **Question Deletion**: Allow users to delete their pending questions
- **Draft Questions**: Save questions locally before submission
- **Rich Text**: Support markdown or basic formatting in question body
- **Attachments**: Allow images/links in questions
- **Question Categories**: Tag questions with topics/subjects
- **Priority Flags**: Mark questions as urgent
- **Moderation**: Host can hide/flag inappropriate questions

## Risks & Mitigations

**Risk**: User ID not persisted across page refreshes  
**Mitigation**: Use sessionStorage to maintain user context. Clear on logout/session end.

**Risk**: Race condition when checking question limit  
**Mitigation**: Count happens inside same transaction as insert. Database constraints prevent over-insertion.

**Risk**: Question feed doesn't update for other participants  
**Mitigation**: MVP uses manual refresh. Phase 11 adds WebSocket for real-time updates.

**Risk**: Spam submissions via header manipulation  
**Mitigation**: MVP accepts security trade-off. Future: proper authentication with signed tokens.

**Risk**: Character counter out of sync with validation  
**Mitigation**: Both use same limit (280). Pydantic validation is source of truth. Client-side is convenience.

**Risk**: Form state lost on navigation  
**Mitigation**: Not implementing draft persistence in MVP. User must stay on page to complete submission.

## Testing Checklist

### Backend Unit Tests
- [ ] Repository: Create question with author
- [ ] Repository: Create question anonymous (NULL author)
- [ ] Repository: Count returns 0 for new user
- [ ] Repository: Count only pending questions
- [ ] Repository: Count filters by session and user
- [ ] Service: Successful submission
- [ ] Service: Session not found error
- [ ] Service: Session not active error (draft)
- [ ] Service: Session not active error (ended)
- [ ] Service: Not participant error
- [ ] Service: Question limit error
- [ ] Service: Empty body error
- [ ] Service: Whitespace-only body error
- [ ] Service: Body trimming
- [ ] Service: Response includes author

### Backend Integration Tests
- [ ] API: 201 with valid submission
- [ ] API: 400 for empty body
- [ ] API: 403 for non-participant
- [ ] API: 403 for limit exceeded
- [ ] API: 404 for invalid session
- [ ] API: 409 for inactive session
- [ ] API: 422 for missing body
- [ ] API: 422 for oversized body
- [ ] API: Response schema validation
- [ ] API: Question appears in GET requests

### Frontend Manual Tests
- [ ] Form renders on session page
- [ ] Character counter updates on input
- [ ] Counter shows warning colors (200, 260)
- [ ] Submit with valid question succeeds
- [ ] Submit with 280 chars succeeds
- [ ] Submit with 281 chars shows client error
- [ ] Submit empty shows client error
- [ ] Submit whitespace shows server error
- [ ] Submit 4th question shows limit error
- [ ] Success message displays and clears
- [ ] Question feed refreshes after submit
- [ ] New question appears at top of feed
- [ ] User ID persists across navigation
- [ ] Form disabled during submission
- [ ] Error messages are user-friendly
- [ ] No console errors during normal flow

## Documentation Updates

**Files to Update**:
1. `docs/api/sessions.md` - Add POST endpoint spec
2. `backend/app/README.md` - Mention question service
3. `backend/app/services/README.md` - Document QuestionService
4. `backend/app/repositories/README.md` - Document new functions
5. `README.md` - Update current capabilities
6. `agent.md` - Update current status and near-term backlog
7. `docs/dev-journal/09-question-submission.md` - Implementation outcomes

---

## Implementation Outcomes

**Status**: Not started  
**Expected Completion**: TBD  
**Test Count Target**: 26+ new tests (7 repository, 10 service, 9 API)

_This section will be updated with implementation details, statistics, and learnings after completion._

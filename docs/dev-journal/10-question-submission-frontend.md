# Question Submission Frontend — Implementation Plan

## Goal

Enable participants to submit questions by implementing UI and handlers that call the existing `POST /sessions/{code}/questions` endpoint.

**User Story**: As a participant, I want to be able to ask questions during a session.

## Prerequisites

**Backend Ready** ✅:
- POST /sessions/{code}/questions endpoint (98 tests passing)
- Requires X-User-Id header and body (1-280 chars)
- Enforces 3 pending question limit per user

**Critical Blocker** ❌:
- Join response returns `session.host.id` (host's ID), not joiner's ID
- Participants would submit questions with wrong user_id
- Backend must return joiner's user_id in response

## Scope

**Implements**:
- Backend: Return joiner's user_id in create/join responses
- Frontend: Store user_id in sessionStorage
- UI: Question form with character counter (0/280)
- Validation: Disable button at 3 pending questions
- Error handling: 403, 409, 422 with friendly messages
- Auto-refresh feed after submission

**Out of Scope**:
- Question editing/deletion
- Voting/liking
- Real-time updates (WebSockets)
- Host moderation

## Architecture Decisions

### 1. User ID Response Strategy

**Problem**: 
- Create response: `session.host.id` works (creator IS host) ✅
- Join response: `session.host.id` is WRONG (returns host's ID, not joiner's) ❌

**Solution**: Return wrapper with current user's ID.

**Implementation**:
```python
# New schema
class SessionWithUserId(BaseModel):
    session: SessionSummary
    user_id: int

# Update join_session service to return (SessionSummary, user_id)
# Update API to wrap response
```

**Frontend**:
```javascript
// Store creator's ID (creator is host)
sessionStorage.setItem('userId', response.user_id);

// Store joiner's ID (from wrapper)
sessionStorage.setItem('userId', response.user_id);
```

### 2. Question Limit UI

**Decision**: Disable submit button at 3 pending questions (client-side count).

**Why**: Better UX than 409 errors, instant feedback.

### 3. Form Placement

**Decision**: Add form above question feed in `session.html`.

**Why**: Natural flow (submit → view).

## Implementation Plan

### Phase 1: Backend Response Wrapper

**Problem**: Join returns host's user_id, not joiner's.

**Files**:
- `backend/app/schemas/sessions.py` - Add `SessionWithUserId` schema
- `backend/app/services/sessions.py` - Modify `create_session()` and `join_session()` to return tuple
- `backend/app/api/routes/sessions.py` - Update endpoints to use new response model

**Schema**:
```python
class SessionWithUserId(BaseModel):
    """Response wrapper including current user's ID."""
    session: SessionSummary
    user_id: int
```

**Service Changes**:
```python
def create_session(...) -> tuple[SessionSummary, int]:
    # ... existing logic ...
    return session_summary, host["id"]

def join_session(...) -> tuple[SessionSummary, int]:
    # ... existing logic ...
    return session_summary, user["id"]  # Joiner's ID, not host's
```

**API Changes**:
```python
@router.post("", response_model=SessionWithUserId, ...)
async def create_session(...) -> SessionWithUserId:
    summary, user_id = service.create_session(...)
    return SessionWithUserId(session=summary, user_id=user_id)

@router.post("/{code}/join", response_model=SessionWithUserId, ...)
async def join_session(...) -> SessionWithUserId:
    summary, user_id = service.join_session(...)
    return SessionWithUserId(session=summary, user_id=user_id)
```

**Tests**: Update API tests to expect new response structure.

---

### Phase 2: API Function

**File**: `frontend/public/js/api.js`

Add `submitQuestion()`:
```javascript
async function submitQuestion(code, userId, body) {
  const response = await fetch(`${API_BASE_URL}/sessions/${code}/questions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': String(userId),
    },
    body: JSON.stringify({ body })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let message = `HTTP ${response.status}`;
    
    if (errorData.detail) {
      message = Array.isArray(errorData.detail) 
        ? errorData.detail[0]?.msg || JSON.stringify(errorData.detail)
        : errorData.detail;
    }
    
    throw new Error(message);
  }
  
  return await response.json();
}
```

---

### Phase 3: User ID Storage

**File**: `frontend/public/js/ui.js`

Update `renderCreateSuccess()` and `renderJoinSuccess()`:
```javascript
// Both functions receive wrapped response now
function renderCreateSuccess(element, response) {
  const session = response.session;  // Unwrap
  
  // Store user ID
  sessionStorage.setItem('userId', response.user_id);
  
  // ... rest of existing code using session ...
}

function renderJoinSuccess(element, response, displayName) {
  const session = response.session;  // Unwrap
  
  // Store user ID
  sessionStorage.setItem('userId', response.user_id);
  
  // ... rest of existing code using session ...
}
```

**Note**: Frontend code calling these functions must be updated to pass wrapped response.

**File**: `frontend/public/js/session.js`

Add utility:
```javascript
function getCurrentUserId() {
  const userId = sessionStorage.getItem('userId');
  return userId ? parseInt(userId, 10) : null;
}
```

---

### Phase 4: HTML Form

**File**: `frontend/public/session.html`

Add before questions section:
```html
<section>
  <h2>Ask a Question</h2>
  <form id="question-form">
    <div class="form-group">
      <label for="question-body">Your Question</label>
      <textarea 
        id="question-body" 
        maxlength="280" 
        placeholder="Type your question here (max 280 characters)..."
        rows="3"
        required
      ></textarea>
      <div class="char-counter">
        <span id="char-count">0</span>/280
      </div>
    </div>
    <div class="form-actions">
      <button type="submit" id="submit-question-btn" class="button">
        Submit Question
      </button>
      <div id="question-limit-warning" class="warning-message" style="display: none;">
        You have 3 pending questions. Wait for answers before submitting more.
      </div>
    </div>
    <div id="question-form-output"></div>
  </form>
</section>
```

---

### Phase 5: CSS Styling

**File**: `frontend/public/css/styles.css`

Add new styles (note: `.success-message` and `button:disabled` already exist):
```css
/* Question Form Textarea */
#question-form textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-family: inherit;
  font-size: 1rem;
  resize: vertical;
  min-height: 80px;
}

#question-form textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Character Counter */
.char-counter {
  text-align: right;
  font-size: 0.875rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.char-counter.warning {
  color: #dc2626;
  font-weight: 600;
}

/* Form Actions */
.form-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
}

/* Warning Message */
.warning-message {
  padding: 0.75rem;
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 4px;
  color: #92400e;
  font-size: 0.875rem;
}
```

---

### Phase 6: Form Handlers

**File**: `frontend/public/js/session.js`

Add form setup:
```javascript
function setupQuestionForm() {
  const form = document.getElementById('question-form');
  const textarea = document.getElementById('question-body');
  const charCount = document.getElementById('char-count');
  const submitBtn = document.getElementById('submit-question-btn');
  const output = document.getElementById('question-form-output');
  const limitWarning = document.getElementById('question-limit-warning');
  
  if (!form || !textarea || !submitBtn) return;
  
  // Character counter
  textarea.addEventListener('input', () => {
    const count = textarea.value.length;
    charCount.textContent = count;
    
    // Visual warning at 260+ characters
    if (count >= 260) {
      charCount.parentElement.classList.add('warning');
    } else {
      charCount.parentElement.classList.remove('warning');
    }
  });
  
  // Check question limit
  function checkQuestionLimit() {
    const userId = getCurrentUserId();
    if (!userId) {
      submitBtn.disabled = true;
      return;
    }
    
    // Count pending questions from feed
    const cards = document.querySelectorAll('.question-card');
    let pendingCount = 0;
    
    cards.forEach(card => {
      const isPending = card.querySelector('.question-status-badge.pending');
      const authorId = card.dataset.authorId;
      
      if (isPending && authorId && parseInt(authorId) === userId) {
        pendingCount++;
      }
    });
    
    submitBtn.disabled = pendingCount >= 3;
    limitWarning.style.display = pendingCount >= 3 ? 'block' : 'none';
  }
  
  // Form submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userId = getCurrentUserId();
    if (!userId) {
      output.innerHTML = '<div class="error-message">User ID not found. Please rejoin the session.</div>';
      return;
    }
    
    const body = textarea.value.trim();
    if (!body) {
      output.innerHTML = '<div class="error-message">Question cannot be empty.</div>';
      return;
    }
    
    // Disable form during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    output.innerHTML = '<div class="loading-message">Submitting your question...</div>';
    
    try {
      await submitQuestion(currentSessionCode, userId, body);
      
      // Success
      output.innerHTML = '<div class="success-message">Question submitted successfully!</div>';
      textarea.value = '';
      charCount.textContent = '0';
      
      // Reload question feed
      setTimeout(async () => {
        output.innerHTML = '';
        const questions = await getSessionQuestions(currentSessionCode, currentFilter);
        renderQuestionFeed(questions);
        checkQuestionLimit();
      }, 1000);
      
    } catch (error) {
      // Map error codes to friendly messages
      const msg = error.message;
      let errorMessage = 'Failed to submit question.';
      
      if (msg.includes('403') || msg.includes('participant')) {
        errorMessage = 'You must be a participant to submit questions.';
      } else if (msg.includes('409') && msg.includes('3 pending')) {
        errorMessage = 'You have 3 pending questions. Wait for answers before submitting more.';
      } else if (msg.includes('422')) {
        errorMessage = 'Invalid question. Check length and content.';
      } else if (msg.includes('404')) {
        errorMessage = 'Session not found.';
      } else {
        errorMessage = msg;
      }
      
      output.innerHTML = `<div class="error-message">${escapeHtml(errorMessage)}</div>`;
      
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Question';
    }
  });
  
  // Initial limit check
  checkQuestionLimit();
}
```

Update `renderQuestionFeed()` - add `data-author-id`:
```javascript
// In the map function, add data attribute to card:
return `
  <div class="question-card" data-author-id="${question.author?.id || null}">
    <!-- existing card content -->
  </div>
`;
```

Update `initializeSessionPage()` - call setup:
```javascript
async function initializeSessionPage() {
  // ... existing code ...
  setupQuestionFilters();
  setupQuestionForm();  // Add this
  await loadSessionData();
}
```

---

## Testing Strategy

**Manual Tests**:
1. User ID storage (create + join)
2. Character counter live updates
3. Submit valid question → success + refresh
4. Submit 3 questions → 4th attempt disabled
5. Error cases: 403, 404, 409, 422, empty userId
6. Button states during submission

---

## Implementation Sequence

1. Phase 1: Backend (schema + service + API + tests)
2. Phase 2: Add `submitQuestion()` to api.js
3. Phase 3: Update ui.js for userId storage
4. Phase 4: HTML form
5. Phase 5: CSS
6. Phase 6: Form handlers
7. Manual testing

**Time**: 3-4 hours

---

## Success Criteria

- [ ] Backend returns joiner's user_id (not host's)
- [ ] Frontend stores userId in sessionStorage
- [ ] Character counter updates live
- [ ] Button disabled at 3 pending questions
- [ ] Questions submit with correct X-User-Id header
- [ ] Feed auto-refreshes after submission
- [ ] Friendly error messages for all cases
- [ ] Form resets on success

---

## Known Limitations

1. **No Real-time Updates**: Manual refresh required to see others' questions (WebSocket future work)
2. **Client-side Counting**: Limit check may desync across tabs
3. **No Offline Queue**: Submissions fail when offline
4. **No Edit/Delete**: Questions immutable after submission

---

## Future Work

- WebSocket real-time updates
- Question editing (5min window)
- Question deletion (own questions)
- Anonymous toggle
- Markdown support

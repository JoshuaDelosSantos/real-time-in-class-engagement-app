# Join Session Frontend — Implementation Plan

## Goal

Implement frontend UI and JavaScript to enable participants to join a classroom session using a session code and display name, calling the existing `POST /sessions/{code}/join` backend endpoint.

## Implementation Plan

### Phase 1: API Function ✅
- Add `joinSession(code, displayName)` to `public/js/api.js`
- Include 422 array handling fix (check `Array.isArray(errorData.detail)`)
- Add JSDoc documentation

### Phase 2: UI Helper Updates ✅
- Update `showLoading(element, message = 'Loading…')` in `public/js/ui.js` to accept optional message parameter
- Verify existing `.error-message` styling in `styles.css`

### Phase 3: HTML Form ✅
- Add join session form section to `index.html`
- Include session code input with `oninput="this.value = this.value.toUpperCase()"`
- Include display name input (1-100 chars)
- Add submit button and output container

### Phase 4: CSS Styling
- Add form styles (`.form-group`, `.success-message`, `.session-details`) to `public/css/styles.css`
- Reuse existing `.error-message` class (do NOT duplicate)
- Ensure mobile responsiveness

### Phase 5: UI Handlers
- Add `setupJoinSession()` to `public/js/ui.js`
- Add DOM node guards at function start
- Add live input transform listener for session code
- Implement form validation (code length, name length)
- Call `showLoading(output, 'Joining session…')` with custom message
- Add `renderJoinSuccess()` helper
- Add `renderJoinError()` helper with friendly messages
- Store session info in sessionStorage
- Update `initializeApp()` to call `setupJoinSession()`

### Phase 6: Testing & Validation
- Test successful join flow
- Test 422 error displays readable message (not "[object Object]")
- Test all error cases (400, 404, 409, 422)
- Test input validation (empty, too long, wrong length code)
- Test live uppercase transformation
- Test idempotent joins (same user/session twice)
- Test form reset after success
- Test sessionStorage persistence
- Verify XSS protection (display name with HTML)
- Verify DOM guard works

### Phase 7: Documentation
- Add implementation outcomes to this document
- Update `docs/frontend-guide.md` if patterns changed

## Code Examples

### API Function (Phase 1)

```javascript
/**
 * Join an existing session as a participant.
 */
async function joinSession(code, displayName) {
  const response = await fetch(`${API_BASE_URL}/sessions/${code}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: displayName })
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

### UI Helper (Phase 2)

```javascript
function showLoading(element, message = 'Loading…') {
  element.innerHTML = `<div class="loading-message">${escapeHtml(message)}</div>`;
}
```

### HTML Form (Phase 3)

```html
<section>
  <h2>Join a Session</h2>
  <form id="join-form">
    <div class="form-group">
      <label for="session-code">Session Code</label>
      <input 
        type="text" 
        id="session-code" 
        placeholder="ABC123" 
        maxlength="6"
        pattern="[A-Z0-9]{6}"
        required
        style="text-transform: uppercase;"
        oninput="this.value = this.value.toUpperCase()"
      />
      <small>Enter the 6-character code provided by your instructor</small>
    </div>
    
    <div class="form-group">
      <label for="display-name">Your Display Name</label>
      <input 
        type="text" 
        id="display-name" 
        placeholder="Student Alice" 
        maxlength="100"
        required
      />
      <small>This is how you'll appear to others (1-100 characters)</small>
    </div>
    
    <button type="submit" id="join-button">Join Session</button>
  </form>
  
  <div id="join-output">Enter a session code and your name to join</div>
</section>
```

### CSS Styles (Phase 4)

```css
/* Form Components */
.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #1e293b;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.375rem;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group small {
  display: block;
  margin-top: 0.25rem;
  color: #64748b;
  font-size: 0.875rem;
}

/* Success Messages */
.success-message {
  background: #d1fae5;
  border-left: 4px solid #10b981;
  padding: 1rem;
  border-radius: 0.375rem;
}

.success-message h3 {
  margin-top: 0;
  color: #065f46;
}

.session-details {
  margin: 1rem 0;
}

.session-details p {
  margin: 0.5rem 0;
  color: #1e293b;
}

.next-steps {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #a7f3d0;
  color: #065f46;
  font-style: italic;
}
```

### UI Handler (Phase 5)

```javascript
function setupJoinSession() {
  const form = document.getElementById('join-form');
  const codeInput = document.getElementById('session-code');
  const nameInput = document.getElementById('display-name');
  const submitButton = document.getElementById('join-button');
  const output = document.getElementById('join-output');
  
  // DOM guards
  if (!form || !codeInput || !nameInput || !submitButton || !output) {
    console.warn('Join session form elements not found, skipping setup');
    return;
  }
  
  // Live input transformation
  codeInput.addEventListener('input', (event) => {
    event.target.value = event.target.value.toUpperCase();
  });
  
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const code = codeInput.value.trim().toUpperCase();
    const displayName = nameInput.value.trim();
    
    // Validation
    if (!code || code.length !== 6) {
      renderError(output, 'Please enter a valid 6-character session code');
      return;
    }
    
    if (!displayName || displayName.length < 1) {
      renderError(output, 'Please enter your display name');
      return;
    }
    
    if (displayName.length > 100) {
      renderError(output, 'Display name must be 100 characters or less');
      return;
    }
    
    // Disable during request
    submitButton.disabled = true;
    codeInput.disabled = true;
    nameInput.disabled = true;
    showLoading(output, 'Joining session…');
    
    try {
      const session = await joinSession(code, displayName);
      
      // Store session info
      sessionStorage.setItem('currentSession', JSON.stringify({
        code: session.code,
        displayName: displayName,
        joinedAt: new Date().toISOString()
      }));
      
      renderJoinSuccess(output, session, displayName);
      form.reset();
      
    } catch (error) {
      renderJoinError(output, error.message);
    } finally {
      submitButton.disabled = false;
      codeInput.disabled = false;
      nameInput.disabled = false;
    }
  });
}

function renderJoinSuccess(element, session, displayName) {
  element.innerHTML = `
    <div class="success-message">
      <h3>✓ Successfully joined!</h3>
      <div class="session-details">
        <p><strong>Session:</strong> ${escapeHtml(session.title)}</p>
        <p><strong>Code:</strong> ${escapeHtml(session.code)}</p>
        <p><strong>Host:</strong> ${escapeHtml(session.host.display_name)}</p>
        <p><strong>Your name:</strong> ${escapeHtml(displayName)}</p>
        <p><strong>Status:</strong> ${escapeHtml(session.status)}</p>
      </div>
      <p class="next-steps">You're now a participant in this session. Question submission coming soon!</p>
    </div>
  `;
}

function renderJoinError(element, errorMessage) {
  const friendlyMessages = {
    'Session not found': 'Invalid session code. Please check and try again.',
    'Session has ended and is no longer joinable': 'This session has ended and is no longer accepting participants.',
    'Display name is required': 'Please enter a display name (cannot be only spaces).',
  };
  
  const displayMessage = friendlyMessages[errorMessage] || errorMessage;
  
  element.innerHTML = `
    <div class="error-message">
      <p><strong>Unable to join session</strong></p>
      <p>${escapeHtml(displayMessage)}</p>
    </div>
  `;
}

// Update initializeApp()
function initializeApp() {
  setupHealthCheck();
  setupSessionsFetch();
  setupJoinSession();
}
```

## Key Decisions

1. **Dual Uppercase Transformation**: Use both CSS (`text-transform`) and JavaScript (`oninput`) for immediate visual feedback and actual value transformation.

2. **422 Error Array Handling**: Pydantic returns validation errors as arrays of objects. Extract `.msg` from first element to show readable messages.

3. **External CSS Only**: All styles go in `styles.css`, not inline in HTML. Maintains separation of concerns.

4. **Defensive Programming**: DOM guards prevent crashes if HTML elements are missing or renamed.

5. **Parameterised Loading Messages**: `showLoading()` accepts optional message for context-specific feedback ("Joining session…" vs "Loading…").

6. **Reuse Existing Styles**: `.error-message` already exists in `styles.css`. Do not duplicate.

7. **sessionStorage Persistence**: Store joined session info for potential future features (e.g., returning users, session history).

8. **Friendly Error Messages**: Map technical API errors to user-friendly messages while preserving unknown errors.

9. **Form Reset After Success**: Clear inputs after successful join to prepare for potential next action.

10. **XSS Protection**: Always use `escapeHtml()` when rendering user-provided data in HTML.

## Success Criteria

- [x] `joinSession()` function implemented with proper error handling
- [x] 422 validation errors display readable messages
- [x] Form displays with proper HTML5 validation
- [x] Live uppercase transformation works
- [ ] Form submission calls API correctly
- [ ] Success message displays session details
- [ ] Error messages are user-friendly
- [ ] sessionStorage stores join info
- [x] All existing features still work
- [ ] No XSS vulnerabilities
- [ ] Mobile responsive design
- [ ] DOM guards prevent runtime errors

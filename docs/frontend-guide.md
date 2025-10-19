# Frontend Developer Guide

Educational guide for working with the ClassEngage frontend codebase.

## Overview

This guide covers essential patterns and best practices for building web UIs that communicate with REST APIs. The examples reference actual code from this project.

## Table of Contents

1. [Working with the Fetch API](#working-with-the-fetch-api)
2. [Error Handling](#error-handling)
3. [Async/Await vs Promises](#asyncawait-vs-promises)
4. [Security: Preventing XSS](#security-preventing-xss)
5. [Loading States & UX](#loading-states--ux)
6. [HTTP Methods](#http-methods)
7. [CORS Considerations](#cors-considerations)
8. [Reusable Form Components](#reusable-form-components)
9. [Page Navigation & Session Continuity](#page-navigation--session-continuity)

---

## Working with the Fetch API

The Fetch API is the modern standard for making HTTP requests from JavaScript. It's built into all modern browsers and returns Promises.

### Basic GET Request

```javascript
// Simple GET request
const response = await fetch('http://localhost:8000/health');
const data = await response.json();
console.log(data);
```

### Checking Response Status

**Important:** `fetch()` only rejects on network failures, NOT HTTP errors like 404 or 500.

```javascript
const response = await fetch(url);

// Always check response.ok (status 200-299)
if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}

const data = await response.json();
```

See `public/js/api.js` for examples: `checkHealth()`, `fetchSessions()`

---

## Error Handling

Always wrap fetch calls in try/catch blocks to handle:
- Network failures (no connection, timeout)
- HTTP errors (4xx, 5xx status codes)
- JSON parsing errors

### Pattern

```javascript
try {
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  const data = await response.json();
  // Process data...
  
} catch (error) {
  console.error('Request failed:', error.message);
  // Show error to user
}
```

See `public/js/ui.js` for UI-level error handling with `renderError()`.

---

## Async/Await vs Promises

`async/await` is syntactic sugar over Promises. These are equivalent:

### Promise Chain

```javascript
fetch(url)
  .then(response => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

### Async/Await

```javascript
try {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

**Recommendation:** Use async/await for cleaner, more readable code.

---

## Security: Preventing XSS

**Never trust API data.** Always escape user-provided content before inserting into the DOM.

### The Problem

```javascript
// ❌ DANGEROUS - allows XSS attacks
element.innerHTML = `<div>${userInput}</div>`;

// If userInput is: <img src=x onerror=alert('XSS')>
// The script will execute!
```

### The Solution

Use `textContent` for plain text:

```javascript
// ✅ SAFE - automatically escapes
element.textContent = userInput;
```

Or use our `escapeHtml()` helper for HTML structures:

```javascript
// ✅ SAFE - escapes special characters
element.innerHTML = `<div>${escapeHtml(userInput)}</div>`;
```

### How `escapeHtml()` Works

```javascript
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;  // Browser escapes automatically
  return div.innerHTML;     // Read back escaped version
}

// Example
escapeHtml('<img src=x onerror=alert(1)>')
// Returns: '&lt;img src=x onerror=alert(1)&gt;'
```

See `public/js/utils.js` for the implementation.

---

## Form Handling Patterns

This section covers best practices for handling form submissions with API calls, based on the join session implementation.

### Complete Form Handler Example

```javascript
function setupJoinSession() {
  const form = document.getElementById('join-form');
  const codeInput = document.getElementById('session-code');
  const nameInput = document.getElementById('display-name');
  const submitButton = document.getElementById('join-button');
  const output = document.getElementById('join-output');
  
  // 1. DOM Guards - prevent crashes if elements missing
  if (!form || !codeInput || !nameInput || !submitButton || !output) {
    console.warn('Join session form elements not found, skipping setup');
    return;
  }
  
  // 2. Live Input Transformation (optional)
  codeInput.addEventListener('input', (event) => {
    event.target.value = event.target.value.toUpperCase();
  });
  
  // 3. Form Submit Handler
  form.addEventListener('submit', async (event) => {
    event.preventDefault();  // Prevent page reload
    
    const code = codeInput.value.trim().toUpperCase();
    const displayName = nameInput.value.trim();
    
    // 4. Client-Side Validation
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
    
    // 5. Disable Inputs During Request (prevent double-submit)
    submitButton.disabled = true;
    codeInput.disabled = true;
    nameInput.disabled = true;
    showLoading(output, 'Joining session…');
    
    try {
      // 6. Make API Call
      const session = await joinSession(code, displayName);
      
      // 7. Store Data (optional)
      sessionStorage.setItem('currentSession', JSON.stringify({
        code: session.code,
        displayName: displayName,
        joinedAt: new Date().toISOString()
      }));
      
      // 8. Show Success & Reset Form
      renderJoinSuccess(output, session, displayName);
      form.reset();
      
    } catch (error) {
      // 9. Show User-Friendly Error
      renderJoinError(output, error.message);
    } finally {
      // 10. Re-enable Inputs
      submitButton.disabled = false;
      codeInput.disabled = false;
      nameInput.disabled = false;
    }
  });
}
```

### Key Form Handling Principles

1. **DOM Guards**: Check all elements exist before setup
2. **Prevent Default**: Always `event.preventDefault()` on form submit
3. **Client-Side Validation**: Validate before API call to save bandwidth
4. **Trim Input**: Use `.trim()` to remove whitespace
5. **Disable During Request**: Prevent double-submission
6. **Loading Feedback**: Show loading state immediately
7. **Error Mapping**: Convert technical errors to user-friendly messages
8. **Form Reset**: Clear inputs after success
9. **Finally Block**: Always re-enable inputs, even on error

See `public/js/ui.js` → `setupJoinSession()` for complete implementation.

---

## Loading States & UX

Always provide feedback during async operations:

### Pattern

```javascript
async function handleButtonClick() {
  // 1. Disable button to prevent duplicate requests
  button.disabled = true;
  
  // 2. Show loading indicator
  output.textContent = 'Loading...';
  
  try {
    const data = await fetchData();
    // 3. Show success state
    renderData(output, data);
  } catch (error) {
    // 4. Show error state
    renderError(output, error.message);
  } finally {
    // 5. Re-enable button
    button.disabled = false;
  }
}
```

See `public/js/ui.js` for `setupHealthCheck()` and `setupSessionsFetch()` implementations.

---

## HTTP Methods

### GET (default)

```javascript
fetch(url)
```

### POST

```javascript
fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'New Session',
    host_display_name: 'Prof. Smith'
  }),
})
```

**Join Session Example** (backend ready, frontend pending):

```javascript
// POST to /sessions/{code}/join
const code = 'ABC123'; // From user input
const response = await fetch(`http://localhost:8000/sessions/${code}/join`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    display_name: 'Student Alice'
  }),
});

if (!response.ok) {
  // Handle errors: 400 (invalid name), 404 (code not found), 
  // 409 (session ended), 422 (validation error)
  throw new Error(`Failed to join: ${response.status}`);
}

const session = await response.json();
// session contains: { id, code, title, status, host, created_at }
```

### Other Methods

```javascript
// PUT
fetch(url, { method: 'PUT', body: JSON.stringify(data) })

// DELETE
fetch(url, { method: 'DELETE' })

// PATCH
fetch(url, { method: 'PATCH', body: JSON.stringify(partialData) })
```

See `public/js/api.js` for `createSession()` POST example. Join session implementation pending.

---

## CORS Considerations

If your frontend runs on a different origin (domain or port) than the backend, the browser enforces Cross-Origin Resource Sharing (CORS) rules.

### Symptoms

```
Access to fetch at 'http://localhost:8000/sessions' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

### Solution

The backend must include CORS headers. FastAPI handles this via middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Development:** Use `allow_origins=["*"]` for local development (never in production).

---

## Reusable Form Components

The ClassEngage frontend uses **component builder functions** to generate HTML for forms dynamically, eliminating hardcoded HTML and ensuring consistency across the application.

### Why Component Builders?

**Problems with Hardcoded HTML:**
- ❌ Duplication across multiple forms
- ❌ Inconsistent styling and structure
- ❌ Difficult to maintain (changes require editing HTML and JS)
- ❌ No type safety or documentation

**Benefits of Component Builders:**
- ✅ DRY (Don't Repeat Yourself) - define structure once
- ✅ Consistency - all forms use same HTML structure
- ✅ Maintainability - change once, affects all forms
- ✅ Type safety - JSDoc provides autocomplete
- ✅ XSS protection - built-in escaping
- ✅ No build tools - pure vanilla JavaScript

### Component Functions

See `public/js/components.js` for implementation.

#### createFormField(config)

Generates a single form field with label, input, and helper text.

```javascript
const fieldHTML = createFormField({
  id: 'session-title',
  label: 'Session Title',
  placeholder: 'e.g., Physics 101',
  maxLength: 200,
  helperText: 'Enter a title (1-200 characters)',
  required: true  // default: true
});
```

**Generated HTML:**
```html
<div class="form-group">
  <label for="session-title">Session Title</label>
  <input type="text" id="session-title" placeholder="e.g., Physics 101" maxlength="200" required />
  <small>Enter a title (1-200 characters)</small>
</div>
```

**Configuration Options:**
- `id` (required) - Input element ID
- `label` (required) - Label text
- `type` (optional, default: 'text') - Input type
- `placeholder` (optional) - Placeholder text
- `maxLength` (optional) - Maximum character length
- `pattern` (optional) - Validation regex pattern
- `required` (optional, default: true) - Whether field is required
- `helperText` (optional) - Small text below input
- `attrs` (optional) - Additional HTML attributes as object

**Advanced: Custom Attributes**

Use `attrs` for inline handlers or custom styling:

```javascript
createFormField({
  id: 'session-code',
  label: 'Session Code',
  maxLength: 6,
  attrs: {
    'style': 'text-transform: uppercase;',
    'oninput': 'this.value = this.value.toUpperCase()'
  }
});
```

#### createFormSection(config)

Generates a complete form section with multiple fields, submit button, and output container.

```javascript
const formHTML = createFormSection({
  id: 'create-form',
  title: 'Create a Session',
  fields: [
    {
      id: 'session-title',
      label: 'Session Title',
      placeholder: 'e.g., Physics 101',
      maxLength: 200,
      helperText: 'Enter a descriptive title'
    },
    {
      id: 'host-name',
      label: 'Your Name (Host)',
      placeholder: 'e.g., Dr. Smith',
      maxLength: 100,
      helperText: 'This is how you\'ll appear as host'
    }
  ],
  submitButtonText: 'Create Session',
  submitButtonId: 'create-button',
  outputId: 'create-output',
  outputInitialText: 'Fill out the form to create a session'
});

// Inject into page
document.getElementById('container').innerHTML = formHTML;
```

**Generated Structure:**
```html
<section>
  <h2>Create a Session</h2>
  <form id="create-form">
    <!-- field 1 -->
    <div class="form-group">...</div>
    <!-- field 2 -->
    <div class="form-group">...</div>
    <button type="submit" id="create-button">Create Session</button>
  </form>
  <div id="create-output">Fill out the form to create a session</div>
</section>
```

### Usage Pattern

**Step 1: Define Form Configuration**

```javascript
function renderDynamicForms() {
  const container = document.getElementById('dynamic-forms');
  if (!container) return;
  
  const myFormHTML = createFormSection({
    id: 'my-form',
    title: 'My Form Title',
    fields: [/* field configs */],
    submitButtonText: 'Submit',
    submitButtonId: 'my-button',
    outputId: 'my-output',
    outputInitialText: 'Initial message'
  });
  
  container.innerHTML = myFormHTML;
}
```

**Step 2: Set Up Event Handlers**

```javascript
function setupMyForm() {
  const form = document.getElementById('my-form');
  const input = document.getElementById('my-input');
  const button = document.getElementById('my-button');
  const output = document.getElementById('my-output');
  
  // DOM guards
  if (!form || !input || !button || !output) {
    console.warn('Form elements not found');
    return;
  }
  
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    // Validation
    const value = input.value.trim();
    if (!value) {
      renderError(output, 'Please enter a value');
      return;
    }
    
    // Disable during request
    button.disabled = true;
    input.disabled = true;
    showLoading(output, 'Processing…');
    
    try {
      const result = await myApiCall(value);
      renderSuccess(output, result);
      form.reset();
    } catch (error) {
      renderError(output, error.message);
    } finally {
      button.disabled = false;
      input.disabled = false;
    }
  });
}
```

**Step 3: Initialize in Order**

```javascript
function initializeApp() {
  renderDynamicForms();  // Create DOM elements first
  setupMyForm();         // Then attach handlers
}
```

### Best Practices

1. **Always call renderDynamicForms() first** - DOM elements must exist before attaching event handlers
2. **Use DOM guards** - Check if elements exist before accessing them
3. **Validate on submit** - Check all inputs before making API calls
4. **Disable during requests** - Prevent double-submission
5. **Reset on success** - Clear form after successful submission
6. **Escape user input** - `escapeHtml()` is built into component builders
7. **Provide helpful messages** - Use `helperText` to guide users

### Real-World Example

See `public/js/ui.js` for complete implementations:
- `renderDynamicForms()` - Defines create and join session forms
- `setupCreateSession()` - Event handler for create form
- `setupJoinSession()` - Event handler for join form

---

## Additional Resources

- **API Documentation:** See `docs/api/sessions.md` for endpoint specifications
- **Code Examples:** Browse `public/js/` for working implementations
- **Component Builders:** See `public/js/components.js` for implementation details
- **MDN Web Docs:** [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)

---

## Quick Reference

| Task | Function | File |
|------|----------|------|
| Escape HTML | `escapeHtml(text)` | `js/utils.js` |
| Create form field | `createFormField(config)` | `js/components.js` ⭐ |
| Create form section | `createFormSection(config)` | `js/components.js` |
| Check health | `checkHealth()` | `js/api.js` |
| Fetch sessions | `fetchSessions(limit)` | `js/api.js` |
| Create session | `createSession(data)` | `js/api.js` |
| Join session | `joinSession(code, displayName)` | `js/api.js` |
| Get session details | `getSessionDetails(code)` | `js/api.js` ⭐ |
| Get participants | `getSessionParticipants(code)` | `js/api.js` ⭐ |
| Get questions | `getSessionQuestions(code, status?)` | `js/api.js` ⭐ |
| Show loading | `showLoading(element, message?)` | `js/ui.js` |
| Show error | `renderError(element, msg)` | `js/ui.js` |
| Render join success | `renderJoinSuccess(element, session, displayName)` | `js/ui.js` |
| Render join error | `renderJoinError(element, errorMessage)` | `js/ui.js` |
| Render create success | `renderCreateSuccess(element, session)` | `js/ui.js` |
| Render create error | `renderCreateError(element, errorMessage)` | `js/ui.js` |

---

## Page Navigation & Session Continuity

The app uses two pages: home (`index.html`) and session (`session.html`). Users automatically navigate between them with visual countdown feedback.

### Auto-Redirect Pattern

After creating or joining a session, users see a success message with a 2-second countdown before automatic redirect:

```javascript
function renderCreateSuccess(element, session) {
  const sessionUrl = `/static/session.html?code=${escapeHtml(session.code)}`;
  
  element.innerHTML = `
    <div class="success-message">
      <h3>✓ Session Created!</h3>
      <p id="redirect-countdown">Redirecting in <strong>2</strong> seconds...</p>
      <a href="${sessionUrl}" class="button">Go Now</a>
    </div>
  `;
  
  // Store session for continuity
  sessionStorage.setItem('currentSession', JSON.stringify(session));
  
  // Auto-redirect with countdown (use setTimeout to ensure DOM updated)
  setTimeout(() => {
    let countdown = 2;
    const countdownElement = element.querySelector('#redirect-countdown');
    
    if (!countdownElement) {
      window.location.href = sessionUrl;
      return;
    }
    
    const interval = setInterval(() => {
      countdown--;
      if (countdown > 0) {
        countdownElement.innerHTML = `Redirecting in <strong>${countdown}</strong> second${countdown !== 1 ? 's' : ''}...`;
      } else {
        countdownElement.innerHTML = 'Redirecting now...';
      }
    }, 1000);
    
    setTimeout(() => {
      clearInterval(interval);
      window.location.href = sessionUrl;
    }, 2000);
  }, 0);
}
```

**Key Points:**
- Use `element.querySelector()` not `document.getElementById()` to avoid ID conflicts
- Wrap countdown in `setTimeout(..., 0)` to ensure DOM has updated
- Provide "Go Now" button to skip countdown
- Store session in sessionStorage for cross-page continuity

### URL Query Parameters

Session page reads the session code from URL query parameters:

```javascript
// In session.js
async function initializeSessionPage() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  
  if (!code) {
    window.location.href = '/';  // Redirect to home if no code
    return;
  }
  
  // Load session data using code
  const [session, participants, questions] = await Promise.all([
    getSessionDetails(code),
    getSessionParticipants(code),
    getSessionQuestions(code)
  ]);
  
  renderSessionHeader(session);
  renderParticipantList(participants);
  renderQuestionFeed(questions);
}
```

### Session Continuity with sessionStorage

Store active session to enable "Continue Session" functionality:

```javascript
// Store when creating/joining
sessionStorage.setItem('currentSession', JSON.stringify({
  code: session.code,
  title: session.title,
  createdAt: new Date().toISOString()
}));

// Restore on home page
function checkActiveSession() {
  const sessionData = sessionStorage.getItem('currentSession');
  if (!sessionData) return;
  
  try {
    const session = JSON.parse(sessionData);
    displayContinueButton(session);
  } catch (error) {
    sessionStorage.removeItem('currentSession');
  }
}
```

See `public/js/ui.js` for complete implementation.


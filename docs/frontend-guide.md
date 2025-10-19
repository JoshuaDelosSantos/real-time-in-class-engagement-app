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

## Additional Resources

- **API Documentation:** See `docs/api/sessions.md` for endpoint specifications
- **Code Examples:** Browse `public/js/` for working implementations
- **MDN Web Docs:** [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)

---

## Quick Reference

| Task | Function | File |
|------|----------|------|
| Escape HTML | `escapeHtml(text)` | `js/utils.js` |
| Check health | `checkHealth()` | `js/api.js` |
| Fetch sessions | `fetchSessions(limit)` | `js/api.js` |
| Create session | `createSession(data)` | `js/api.js` |
| Join session | `joinSession(code, displayName)` | `js/api.js` |
| Show loading | `showLoading(element, message?)` | `js/ui.js` |
| Show error | `renderError(element, msg)` | `js/ui.js` |
| Render join success | `renderJoinSuccess(element, session, displayName)` | `js/ui.js` |
| Render join error | `renderJoinError(element, errorMessage)` | `js/ui.js` |


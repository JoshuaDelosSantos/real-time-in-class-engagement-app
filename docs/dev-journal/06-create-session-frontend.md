# Create Session Frontend — Implementation Plan

## Goal

Implement frontend UI and JavaScript to enable users (hosts/instructors) to create classroom sessions, calling the existing `POST /sessions` backend endpoint. This completes the session lifecycle UI, allowing non-technical users to create sessions without using curl/Postman.

**Architectural Decision**: Use reusable form component builders to avoid hardcoding forms in HTML, enabling consistency and maintainability across all forms in the application.

## Implementation Plan

### Phase 1: Reusable Form Components
- Create `public/js/components.js` with form builder functions
- Add `createFormField(config)` - generates individual form fields
- Add `createFormSection(config)` - generates complete form sections
- Include JSDoc documentation for type safety
- Load in `index.html` before `ui.js` (dependency order: utils → components → api → ui)

### Phase 2: Refactor Existing Forms
- Update `index.html` to add dynamic forms container
- Update `ui.js` to add `renderDynamicForms()` function
- Refactor join session form to use `createFormSection()`
- Maintain backward compatibility (same IDs, same structure)
- Verify existing join session functionality still works

### Phase 3: Create Session Form & Handlers
- Add create session form config to `renderDynamicForms()` in `ui.js`
- Add `setupCreateSession()` handler function
- Add DOM node guards at function start
- Implement form validation (title length, name length)
- Call `showLoading(output, 'Creating session…')` with custom message
- Add `renderCreateSuccess()` helper to display session code prominently
- Add `renderCreateError()` helper with friendly messages
- Store created session in sessionStorage (for host tracking)
- Update `initializeApp()` to call `setupCreateSession()` and `renderDynamicForms()`

### Phase 4: CSS Styling
- Reuse existing `.form-group` styles (already compatible)
- Add `.session-code-display` style for prominent code presentation
- Add `.code-large` style for large monospace code text
- Ensure mobile responsiveness

### Phase 5: Documentation
- Add implementation outcomes to this document
- Update `docs/frontend-guide.md` with component pattern documentation
- Document form builder usage for future developers

## Code Examples

### Form Components (Phase 1)

```javascript
// File: frontend/public/js/components.js

/**
 * Reusable UI Components
 * 
 * Functions that generate common UI patterns.
 * Depends on: utils.js
 */

/**
 * Create a form field (label + input + helper text)
 * 
 * @param {Object} config - Field configuration
 * @param {string} config.id - Input element ID
 * @param {string} config.label - Label text
 * @param {string} config.type - Input type (default: 'text')
 * @param {string} [config.placeholder] - Placeholder text
 * @param {number} [config.maxLength] - Maximum character length
 * @param {string} [config.pattern] - Validation pattern
 * @param {boolean} [config.required=true] - Whether field is required
 * @param {string} [config.helperText] - Small text below input
 * @param {Object} [config.attrs] - Additional HTML attributes
 * @returns {string} HTML string for form field
 */
function createFormField(config) {
  const {
    id,
    label,
    type = 'text',
    placeholder = '',
    maxLength,
    pattern,
    required = true,
    helperText,
    attrs = {}
  } = config;
  
  // Build attributes string
  const attributes = [
    `type="${type}"`,
    `id="${id}"`,
    placeholder ? `placeholder="${escapeHtml(placeholder)}"` : '',
    maxLength ? `maxlength="${maxLength}"` : '',
    pattern ? `pattern="${pattern}"` : '',
    required ? 'required' : '',
    ...Object.entries(attrs).map(([key, val]) => `${key}="${val}"`)
  ].filter(Boolean).join(' ');
  
  return `
    <div class="form-group">
      <label for="${id}">${escapeHtml(label)}</label>
      <input ${attributes} />
      ${helperText ? `<small>${escapeHtml(helperText)}</small>` : ''}
    </div>
  `;
}

/**
 * Create a complete form with multiple fields
 * 
 * @param {Object} config - Form configuration
 * @param {string} config.id - Form element ID
 * @param {string} config.title - Form section title
 * @param {Array<Object>} config.fields - Array of field configs (for createFormField)
 * @param {string} config.submitButtonText - Text for submit button
 * @param {string} config.submitButtonId - ID for submit button
 * @param {string} config.outputId - ID for output/result container
 * @param {string} [config.outputInitialText] - Initial text in output container
 * @returns {string} HTML string for complete form section
 */
function createFormSection(config) {
  const {
    id,
    title,
    fields,
    submitButtonText,
    submitButtonId,
    outputId,
    outputInitialText = ''
  } = config;
  
  const fieldsHTML = fields.map(fieldConfig => createFormField(fieldConfig)).join('');
  
  return `
    <section>
      <h2>${escapeHtml(title)}</h2>
      <form id="${id}">
        ${fieldsHTML}
        <button type="submit" id="${submitButtonId}">${escapeHtml(submitButtonText)}</button>
      </form>
      <div id="${outputId}">${escapeHtml(outputInitialText)}</div>
    </section>
  `;
}
```

### Updated HTML Structure (Phase 2)

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ClassEngage</title>
    <link rel="stylesheet" href="/static/css/styles.css" />
  </head>
  <body>
    <!-- Static sections -->
    <section>
      <h1>ClassEngage Health Check</h1>
      <h2>API Status</h2>
      <button id="ping">Check Health</button>
      <pre id="output">Click the button to fetch /health</pre>
    </section>

    <section>
      <h2>Available Sessions</h2>
      <button id="fetch-sessions">Fetch Sessions</button>
      <div id="sessions-output">Click the button to load sessions</div>
    </section>

    <!-- Dynamic forms injected here by JavaScript -->
    <div id="dynamic-forms"></div>

    <!-- Load scripts in dependency order: utils → components → api → ui -->
    <script src="/static/js/utils.js"></script>
    <script src="/static/js/components.js"></script>
    <script src="/static/js/api.js"></script>
    <script src="/static/js/ui.js"></script>
  </body>
</html>
```

### Render Dynamic Forms (Phase 2)

```javascript
// File: frontend/public/js/ui.js

/**
 * Render dynamic form sections using component builders
 */
function renderDynamicForms() {
  const container = document.getElementById('dynamic-forms');
  if (!container) {
    console.warn('Dynamic forms container not found');
    return;
  }
  
  // Create Session Form
  const createSessionHTML = createFormSection({
    id: 'create-form',
    title: 'Create a Session',
    fields: [
      {
        id: 'session-title',
        label: 'Session Title',
        placeholder: 'e.g., Physics 101 - Lecture 3',
        maxLength: 200,
        helperText: 'Enter a descriptive title for your session (1-200 characters)'
      },
      {
        id: 'host-name',
        label: 'Your Name (Host)',
        placeholder: 'e.g., Dr. Smith',
        maxLength: 100,
        helperText: 'This is how you\'ll appear as the session host (1-100 characters)'
      }
    ],
    submitButtonText: 'Create Session',
    submitButtonId: 'create-button',
    outputId: 'create-output',
    outputInitialText: 'Fill out the form above to create a new session'
  });
  
  // Join Session Form (refactored from hardcoded HTML)
  const joinSessionHTML = createFormSection({
    id: 'join-form',
    title: 'Join a Session',
    fields: [
      {
        id: 'session-code',
        label: 'Session Code',
        placeholder: 'ABC123',
        maxLength: 6,
        pattern: '[A-Z0-9]{6}',
        helperText: 'Enter the 6-character code provided by your instructor',
        attrs: {
          'style': 'text-transform: uppercase;',
          'oninput': 'this.value = this.value.toUpperCase()'
        }
      },
      {
        id: 'display-name',
        label: 'Your Display Name',
        placeholder: 'Student Alice',
        maxLength: 100,
        helperText: 'This is how you\'ll appear to others (1-100 characters)'
      }
    ],
    submitButtonText: 'Join Session',
    submitButtonId: 'join-button',
    outputId: 'join-output',
    outputInitialText: 'Enter a session code and your name to join'
  });
  
  // Inject both forms
  container.innerHTML = createSessionHTML + joinSessionHTML;
}
```

### Create Session Handler (Phase 3)

```javascript
function setupCreateSession() {
  const form = document.getElementById('create-form');
  const titleInput = document.getElementById('session-title');
  const hostNameInput = document.getElementById('host-name');
  const submitButton = document.getElementById('create-button');
  const output = document.getElementById('create-output');
  
  // DOM guards
  if (!form || !titleInput || !hostNameInput || !submitButton || !output) {
    console.warn('Create session form elements not found, skipping setup');
    return;
  }
  
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const title = titleInput.value.trim();
    const hostName = hostNameInput.value.trim();
    
    // Validation
    if (!title || title.length < 1) {
      renderError(output, 'Please enter a session title');
      return;
    }
    
    if (title.length > 200) {
      renderError(output, 'Session title must be 200 characters or less');
      return;
    }
    
    if (!hostName || hostName.length < 1) {
      renderError(output, 'Please enter your name as host');
      return;
    }
    
    if (hostName.length > 100) {
      renderError(output, 'Host name must be 100 characters or less');
      return;
    }
    
    // Disable during request
    submitButton.disabled = true;
    titleInput.disabled = true;
    hostNameInput.disabled = true;
    showLoading(output, 'Creating session…');
    
    try {
      const session = await createSession({
        title: title,
        host_display_name: hostName
      });
      
      // Store created session info
      sessionStorage.setItem('createdSession', JSON.stringify({
        code: session.code,
        title: session.title,
        hostName: hostName,
        createdAt: new Date().toISOString()
      }));
      
      renderCreateSuccess(output, session);
      form.reset();
      
    } catch (error) {
      renderCreateError(output, error.message);
    } finally {
      submitButton.disabled = false;
      titleInput.disabled = false;
      hostNameInput.disabled = false;
    }
  });
}

function renderCreateSuccess(element, session) {
  element.innerHTML = `
    <div class="success-message">
      <h3>✓ Session Created!</h3>
      <div class="session-code-display">
        <p><strong>Session Code:</strong></p>
        <p class="code-large">${escapeHtml(session.code)}</p>
      </div>
      <div class="session-details">
        <p><strong>Title:</strong> ${escapeHtml(session.title)}</p>
        <p><strong>Host:</strong> ${escapeHtml(session.host.display_name)}</p>
        <p><strong>Status:</strong> ${escapeHtml(session.status)}</p>
      </div>
      <p class="next-steps">Share this code with participants so they can join your session!</p>
    </div>
  `;
}

function renderCreateError(element, errorMessage) {
  const friendlyMessages = {
    'Host has reached the maximum number of active sessions': 'You have reached the maximum of 3 active sessions. Please end an existing session before creating a new one.',
    'Host display name is required': 'Please enter your name as the session host.',
  };
  
  const displayMessage = friendlyMessages[errorMessage] || errorMessage;
  
  element.innerHTML = `
    <div class="error-message">
      <p><strong>Unable to create session</strong></p>
      <p>${escapeHtml(displayMessage)}</p>
    </div>
  `;
}

// Update initializeApp()
function initializeApp() {
  renderDynamicForms();  // Inject forms first
  setupHealthCheck();
  setupCreateSession();
  setupSessionsFetch();
  setupJoinSession();
}
```

### CSS Styles (Phase 4)

```css
/* Session Code Display (prominent presentation) */
.session-code-display {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f0f9ff;
  border: 2px solid #3b82f6;
  border-radius: 0.5rem;
  text-align: center;
}

.session-code-display p {
  margin: 0.5rem 0;
  color: #1e293b;
}

.code-large {
  font-size: 2rem;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: #1e40af;
  letter-spacing: 0.2em;
  user-select: all;
}
```

## Key Decisions

1. **Reusable Form Components**: Create form builder functions (`createFormField`, `createFormSection`) to eliminate hardcoded HTML and ensure consistency across all forms. This reduces duplication and makes forms easier to maintain.

2. **Refactor Existing Forms**: Migrate the join session form from hardcoded HTML to use the component builder, demonstrating the pattern for future forms.

3. **Form Placement**: Position create session form at the top of dynamic forms (before join session) since creating is the first step in the user flow.

4. **Session Code Prominence**: Display the generated session code in large, monospace font with high contrast to ensure visibility and easy sharing.

5. **Host Name Persistence**: Store host name in sessionStorage after first use to auto-populate in future session creations (UX improvement - deferred to future enhancement).

6. **Error Mapping**: Map the "3 active sessions limit" error to a user-friendly message explaining the constraint.

7. **Form Reset**: Clear form after successful creation to allow quick creation of multiple sessions.

8. **Visual Hierarchy**: Use blue accent colors for session code display (different from green success/red error) to differentiate information type.

9. **Copy Affordance**: Use `user-select: all` CSS to make the session code easily selectable for copying.

10. **Dependency Order**: Load `components.js` after `utils.js` but before `ui.js` to ensure form builder functions are available when needed.

## Success Criteria

- [ ] Create session form displays with proper HTML5 validation
- [ ] Form submission calls API correctly
- [ ] Success message displays session code prominently
- [ ] Error messages are user-friendly
- [ ] sessionStorage stores created session info
- [ ] All existing features still work
- [ ] No XSS vulnerabilities
- [ ] Mobile responsive design
- [ ] DOM guards prevent runtime errors
- [ ] Session code is easily readable and selectable

## Dependencies

- ✅ Backend endpoint `POST /sessions` (fully implemented, 14 tests passing)
- ✅ API function `createSession()` exists in `frontend/public/js/api.js`
- ✅ Helper functions: `escapeHtml()`, `showLoading()`, `renderError()`
- ✅ CSS classes: `.form-group`, `.success-message`, `.error-message`


/**
 * UI Logic & DOM Manipulation
 * 
 * Functions that handle rendering and user interactions.
 * Depends on: utils.js, api.js
 */

/**
 * Initialize the application by setting up event listeners.
 * Call this when the DOM is ready.
 */
function initializeApp() {
  renderDynamicForms();
  setupCreateSession();
  setupJoinSession();
  setupHealthCheck();
  setupSessionsFetch();
  checkActiveSession();
}

/**
 * Render dynamic form sections using component builders.
 * Creates join session form (and future forms) using reusable components.
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
  

  // Only show the correct form depending on page
  const path = window.location.pathname;
  let htmlToRender = '';

  if (path.includes('start.html')) {
    htmlToRender = createSessionHTML;
  } else if (path.includes('join.html')) {
    htmlToRender = joinSessionHTML;
  } else {
    htmlToRender = createSessionHTML + joinSessionHTML;
  }

  container.innerHTML = htmlToRender;
}


  // Inject both forms
  // container.innerHTML = createSessionHTML + joinSessionHTML;
// }

/**
 * Set up the health check button and handler.
 */
function setupHealthCheck() {
  const button = document.getElementById('ping');
  const output = document.getElementById('output');
  
  button.addEventListener('click', async () => {
    // Show loading state
    output.textContent = 'Checking…';
    button.disabled = true;
    
    try {
      const data = await checkHealth();
      renderHealthStatus(output, data);
    } catch (error) {
      renderError(output, error.message);
    } finally {
      button.disabled = false;
    }
  });
}

/**
 * Set up the fetch sessions button and handler.
 */
function setupSessionsFetch() {
  const button = document.getElementById('fetch-sessions');
  const output = document.getElementById('sessions-output');
  
  button.addEventListener('click', async () => {
    // Show loading state
    showLoading(output);
    button.disabled = true;
    
    try {
      const sessions = await fetchSessions();
      renderSessions(output, sessions);
    } catch (error) {
      renderError(output, error.message);
    } finally {
      button.disabled = false;
    }
  });
}

/**
 * Set up the create session form and handler.
 */
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

/**
 * Set up the join session form and handler.
 */
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

/**
 * Render health check status as formatted JSON.
 * 
 * @param {HTMLElement} element - Target element for output
 * @param {Object} data - Health status data
 */
function renderHealthStatus(element, data) {
  element.textContent = JSON.stringify(data, null, 2);
}

/**
 * Render sessions list or empty state message.
 * 
 * @param {HTMLElement} element - Target container element
 * @param {Array} sessions - Array of session objects
 */
function renderSessions(element, sessions) {
  if (sessions.length === 0) {
    element.innerHTML = '<div class="empty-message">No sessions available</div>';
    return;
  }
  
  const sessionCards = sessions.map(session => `
    <div class="session-card">
      <div class="session-title">${escapeHtml(session.title)}</div>
      <div class="session-meta">
        Code: <strong>${escapeHtml(session.code)}</strong> • 
        Host: ${escapeHtml(session.host.display_name)} • 
        Status: ${escapeHtml(session.status)}
      </div>
    </div>
  `).join('');
  
  element.innerHTML = `<div class="session-list">${sessionCards}</div>`;
}

/**
 * Show loading state in an element.
 * 
 * @param {HTMLElement} element - Target element
 * @param {string} [message='Loading…'] - Loading message to display
 */
function showLoading(element, message = 'Loading…') {
  element.innerHTML = `<div class="loading-message">${escapeHtml(message)}</div>`;
}

/**
 * Render an error message.
 * 
 * @param {HTMLElement} element - Target element
 * @param {string} message - Error message to display
 */
function renderError(element, message) {
  element.innerHTML = `<div class="error-message">Error: ${escapeHtml(message)}</div>`;
}

/**
 * Render successful create session result.
 * 
 * @param {HTMLElement} element - Target element
 * @param {Object} session - Created session object from API
 */
function renderCreateSuccess(element, session) {
  const sessionUrl = `/static/session.html?code=${escapeHtml(session.code)}`;
  
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
      <div class="next-steps">
        <p>Share the session code above with your students to let them join!</p>
        <p id="redirect-countdown">Redirecting to session in <strong>2</strong> seconds...</p>
        <a href="${sessionUrl}" class="button">View Session Now</a>
      </div>
    </div>
  `;
  
  // Store session in sessionStorage
  sessionStorage.setItem('currentSession', JSON.stringify(session));
  
  // Auto-redirect with countdown (use setTimeout to ensure DOM is updated)
  setTimeout(() => {
    let countdown = 2;
    const countdownElement = element.querySelector('#redirect-countdown');
    
    if (!countdownElement) {
      console.warn('Countdown element not found, redirecting immediately');
      window.location.href = sessionUrl;
      return;
    }
    
    const countdownInterval = setInterval(() => {
      countdown--;
      if (countdownElement) {
        if (countdown > 0) {
          countdownElement.innerHTML = `Redirecting to session in <strong>${countdown}</strong> second${countdown !== 1 ? 's' : ''}...`;
        } else {
          countdownElement.innerHTML = 'Redirecting now...';
        }
      }
    }, 1000);
    
    setTimeout(() => {
      clearInterval(countdownInterval);
      console.log('Redirecting to session page (create):', sessionUrl);
      window.location.href = sessionUrl;
    }, 2000);
  }, 0);
}

/**
 * Render create session error.
 * 
 * @param {HTMLElement} element - Target element
 * @param {string} errorMessage - Error message from API
 */
function renderCreateError(element, errorMessage) {
  const friendlyMessages = {
    'Host has reached maximum active sessions limit (3)': 'You\'ve reached the maximum of 3 active sessions. Please end an existing session before creating a new one.',
  };
  
  const displayMessage = friendlyMessages[errorMessage] || errorMessage;
  
  element.innerHTML = `
    <div class="error-message">
      <p><strong>Unable to create session</strong></p>
      <p>${escapeHtml(displayMessage)}</p>
    </div>
  `;
}

/**
 * Render successful join session result.
 * 
 * @param {HTMLElement} element - Target element
 * @param {Object} session - Session summary object from API
 * @param {string} displayName - User's display name
 */
function renderJoinSuccess(element, session, displayName) {
  const sessionUrl = `/static/session.html?code=${escapeHtml(session.code)}`;
  
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
      <p class="next-steps">
        <span id="redirect-countdown">Redirecting to session in <strong>2</strong> seconds...</span><br>
        <a href="${sessionUrl}" class="button">Go to Session Now</a>
      </p>
    </div>
  `;
  
  // Store session in sessionStorage
  sessionStorage.setItem('currentSession', JSON.stringify(session));
  
  // Auto-redirect with countdown (use setTimeout to ensure DOM is updated)
  setTimeout(() => {
    let countdown = 2;
    const countdownElement = element.querySelector('#redirect-countdown');
    
    if (!countdownElement) {
      console.warn('Countdown element not found, redirecting immediately');
      window.location.href = sessionUrl;
      return;
    }
    
    const countdownInterval = setInterval(() => {
      countdown--;
      if (countdownElement) {
        if (countdown > 0) {
          countdownElement.innerHTML = `Redirecting to session in <strong>${countdown}</strong> second${countdown !== 1 ? 's' : ''}...`;
        } else {
          countdownElement.innerHTML = 'Redirecting now...';
        }
      }
    }, 1000);
    
    setTimeout(() => {
      clearInterval(countdownInterval);
      console.log('Redirecting to session page (join):', sessionUrl);
      window.location.href = sessionUrl;
    }, 2000);
  }, 0);
}

/**
 * Render join session error with friendly messages.
 * 
 * @param {HTMLElement} element - Target element
 * @param {string} errorMessage - Error message from API
 */
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

/**
 * Check for active session in sessionStorage and display "Continue Session" button.
 */
function checkActiveSession() {
  const sessionSection = document.getElementById('active-session-section');
  const sessionInfo = document.getElementById('active-session-info');
  
  if (!sessionSection || !sessionInfo) return;
  
  const sessionData = sessionStorage.getItem('currentSession');
  if (!sessionData) return;
  
  try {
    const session = JSON.parse(sessionData);
    sessionSection.style.display = 'block';
    sessionInfo.innerHTML = `
      <div class="session-card">
        <div class="session-title">${escapeHtml(session.title)}</div>
        <div class="session-meta">Code: ${escapeHtml(session.code)}</div>
        <a href="/static/session.html?code=${escapeHtml(session.code)}" class="button">Continue Session</a>
      </div>
    `;
  } catch (error) {
    console.error('Failed to parse session data:', error);
    sessionStorage.removeItem('currentSession');
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}

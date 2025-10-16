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
  setupHealthCheck();
  setupSessionsFetch();
}

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
 */
function showLoading(element) {
  element.innerHTML = '<div class="loading-message">Loading sessions…</div>';
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

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}

/**
 * API Layer
 * 
 * Centralized functions for communicating with the backend API.
 * All functions return promises and handle HTTP errors consistently.
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Check the health status of the API.
 * 
 * @returns {Promise<Object>} Health status data
 * @throws {Error} If the request fails or returns non-2xx status
 * 
 * @example
 * const health = await checkHealth();
 * console.log(health.status); // "ok"
 */
async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Fetch recent joinable sessions.
 * 
 * @param {number} [limit=10] - Maximum number of sessions to return
 * @returns {Promise<Array>} Array of session objects
 * @throws {Error} If the request fails or returns non-2xx status
 * 
 * @example
 * const sessions = await fetchSessions(5);
 * console.log(sessions[0].title); // "Introduction to Python"
 */
async function fetchSessions(limit = 10) {
  const url = new URL(`${API_BASE_URL}/sessions`);
  url.searchParams.set('limit', limit);
  
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Create a new session.
 * 
 * @param {Object} sessionData - Session creation payload
 * @param {string} sessionData.title - Session title (1-200 chars)
 * @param {string} sessionData.host_display_name - Host name (1-100 chars)
 * @returns {Promise<Object>} Created session summary
 * @throws {Error} If the request fails or validation errors occur
 * 
 * @example
 * const session = await createSession({
 *   title: 'Web Development 101',
 *   host_display_name: 'Prof. Smith'
 * });
 * console.log(session.code); // "ABC123"
 */
async function createSession(sessionData) {
  const response = await fetch(`${API_BASE_URL}/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(sessionData),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Join an existing session as a participant.
 * 
 * @param {string} code - The 6-character session join code
 * @param {string} displayName - The participant's display name (1-100 chars)
 * @returns {Promise<Object>} Session summary object
 * @throws {Error} If the request fails or returns non-2xx status
 * 
 * @example
 * const session = await joinSession('ABC123', 'Student Alice');
 * console.log(session.title); // "Physics 301"
 */
async function joinSession(code, displayName) {
  const response = await fetch(`${API_BASE_URL}/sessions/${code}/join`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      display_name: displayName
    })
  });
  
  if (!response.ok) {
    // Extract error detail from response body if available
    const errorData = await response.json().catch(() => ({}));
    let message = `HTTP ${response.status}`;
    
    // Handle both string and array formats (422 returns array)
    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        // Pydantic validation errors return array of objects
        message = errorData.detail[0]?.msg || JSON.stringify(errorData.detail);
      } else {
        // Other errors return string
        message = errorData.detail;
      }
    }
    
    throw new Error(message);
  }
  
  return await response.json();
}

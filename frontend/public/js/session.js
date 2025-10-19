/**
 * Session Page Logic
 * 
 * Handles loading and rendering session details, participants, and questions.
 * Depends on: utils.js, api.js
 */

let currentSessionCode = null;
let currentFilter = null; // null = all, 'pending', 'answered'

/**
 * Initialize the session page
 */
async function initializeSessionPage() {
  // Get session code from URL query parameter
  const urlParams = new URLSearchParams(window.location.search);
  currentSessionCode = urlParams.get('code');
  
  if (!currentSessionCode) {
    // No session code provided, redirect to home
    window.location.href = '/';
    return;
  }
  
  // Set up filter buttons
  setupQuestionFilters();
  
  // Load all session data
  await loadSessionData();
}

/**
 * Load all session data
 */
async function loadSessionData() {
  try {
    // Load session details, participants, and questions in parallel
    const [sessionDetails, participants, questions] = await Promise.all([
      getSessionDetails(currentSessionCode),
      getSessionParticipants(currentSessionCode),
      getSessionQuestions(currentSessionCode, currentFilter)
    ]);
    
    // Render all sections
    renderSessionHeader(sessionDetails);
    renderParticipantList(participants);
    renderQuestionFeed(questions);
    
  } catch (error) {
    // Handle session not found or other errors
    if (error.message.includes('not found') || error.message.includes('404')) {
      renderSessionNotFound();
    } else {
      renderSessionError(error.message);
    }
  }
}

/**
 * Render session header with title, code, and status
 */
function renderSessionHeader(session) {
  const headerElement = document.getElementById('session-header');
  if (!headerElement) return;
  
  headerElement.innerHTML = `
    <div class="session-header">
      <div class="session-title-block">
        <h1>${escapeHtml(session.title)}</h1>
        <div class="session-meta">
          <span>Code: <span class="session-code-display">${escapeHtml(session.code)}</span></span>
          <span>Host: ${escapeHtml(session.host.display_name)}</span>
        </div>
      </div>
      <div class="status-badge ${session.status}">${escapeHtml(session.status)}</div>
    </div>
  `;
}

/**
 * Render participant list with host first
 */
function renderParticipantList(participants) {
  const listElement = document.getElementById('participants-list');
  if (!listElement) return;
  
  if (participants.length === 0) {
    listElement.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">👥</div>
        <div class="empty-state-message">No participants yet</div>
        <div class="empty-state-hint">Share the session code to invite others</div>
      </div>
    `;
    return;
  }
  
  const participantHTML = participants.map(participant => {
    const roleClass = participant.role === 'host' ? 'host' : 'participant';
    return `
      <div class="participant-item ${roleClass}">
        <span class="participant-name">${escapeHtml(participant.user.display_name)}</span>
        <span class="participant-role ${roleClass}">${escapeHtml(participant.role)}</span>
      </div>
    `;
  }).join('');
  
  listElement.innerHTML = `<div class="participant-list">${participantHTML}</div>`;
}

/**
 * Render question feed (newest first)
 */
function renderQuestionFeed(questions) {
  const feedElement = document.getElementById('questions-feed');
  if (!feedElement) return;
  
  if (questions.length === 0) {
    const emptyMessage = currentFilter === 'pending' 
      ? 'No pending questions'
      : currentFilter === 'answered'
      ? 'No answered questions yet'
      : 'No questions yet';
    
    const emptyHint = currentFilter 
      ? 'Try selecting a different filter'
      : 'Questions will appear here once submitted';
    
    feedElement.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">💬</div>
        <div class="empty-state-message">${emptyMessage}</div>
        <div class="empty-state-hint">${emptyHint}</div>
      </div>
    `;
    return;
  }
  
  const questionHTML = questions.map(question => {
    const authorText = question.author 
      ? escapeHtml(question.author.display_name)
      : 'Anonymous';
    
    const timestamp = new Date(question.created_at).toLocaleString();
    
    return `
      <div class="question-card">
        <div class="question-header">
          <span class="question-author">${authorText}</span>
          <span class="question-status-badge ${question.status}">${escapeHtml(question.status)}</span>
        </div>
        <div class="question-body">${escapeHtml(question.body)}</div>
        <div class="question-meta">
          <span>${timestamp}</span>
          <span>❤️ ${question.likes}</span>
        </div>
      </div>
    `;
  }).join('');
  
  feedElement.innerHTML = `<div class="question-feed">${questionHTML}</div>`;
}

/**
 * Set up question filter buttons
 */
function setupQuestionFilters() {
  const filterButtons = {
    'filter-all': null,
    'filter-pending': 'pending',
    'filter-answered': 'answered'
  };
  
  Object.entries(filterButtons).forEach(([buttonId, filterValue]) => {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    button.addEventListener('click', async () => {
      // Update active state
      document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
      });
      button.classList.add('active');
      
      // Update filter and reload questions
      currentFilter = filterValue;
      
      const feedElement = document.getElementById('questions-feed');
      if (feedElement) {
        feedElement.innerHTML = '<div class="loading-message">Loading questions...</div>';
      }
      
      try {
        const questions = await getSessionQuestions(currentSessionCode, currentFilter);
        renderQuestionFeed(questions);
      } catch (error) {
        feedElement.innerHTML = `<div class="error-message">Failed to load questions: ${escapeHtml(error.message)}</div>`;
      }
    });
  });
}

/**
 * Render session not found error
 */
function renderSessionNotFound() {
  const headerElement = document.getElementById('session-header');
  if (headerElement) {
    headerElement.innerHTML = `
      <div class="error-message">
        <h2>Session Not Found</h2>
        <p>The session code "${escapeHtml(currentSessionCode)}" does not exist or has ended.</p>
        <a href="/" class="button">Return to Home</a>
      </div>
    `;
  }
  
  // Clear other sections
  const participantsList = document.getElementById('participants-list');
  const questionsFeed = document.getElementById('questions-feed');
  
  if (participantsList) participantsList.innerHTML = '';
  if (questionsFeed) questionsFeed.innerHTML = '';
}

/**
 * Render generic error
 */
function renderSessionError(message) {
  const headerElement = document.getElementById('session-header');
  if (headerElement) {
    headerElement.innerHTML = `
      <div class="error-message">
        <h2>Error Loading Session</h2>
        <p>${escapeHtml(message)}</p>
        <a href="/" class="button">Return to Home</a>
      </div>
    `;
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeSessionPage);
} else {
  initializeSessionPage();
}

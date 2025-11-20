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
  const sessionUrl = `/static/class-discussion-host.html?code=${escapeHtml(session.code)}`;
  
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
  const sessionUrl = `/static/class-discussion-student.html?code=${escapeHtml(session.code)}`;
  
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
        <a href="/static/class-discussion-student.html?code=${escapeHtml(session.code)}" class="button">Continue Session</a>
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

// Initialize class discussion pages (host and student)
if (window.location.pathname.includes('class-discussion')) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeClassDiscussion);
  } else {
    initializeClassDiscussion();
  }
}

/**
 * Initialize class discussion page - loads session data and sets up UI
 */
async function initializeClassDiscussion() {
  const urlParams = new URLSearchParams(window.location.search);
  const sessionCode = urlParams.get('code');
  
  if (!sessionCode) {
    console.error('No session code provided');
    return;
  }
  
  try {
    // Load session data and populate header
    const session = await getSessionDetails(sessionCode);
    updateSessionHeader(session);
    
    // If on host page, populate the lecturer participant card
    if (window.location.pathname.includes('class-discussion-host')) {
      populateLecturerCard(session);
    }
    
  } catch (error) {
    console.error('Failed to load session data:', error);
  }
}

/**
 * Update session header with real data
 */
function updateSessionHeader(session) {
  const sessionNameEl = document.querySelector('.session-name');
  const lecturerNameEl = document.querySelector('.lecturer-name');
  const studentCountEl = document.querySelector('.student-count span:last-child');
  
  if (sessionNameEl) {
    sessionNameEl.textContent = `Session: ${session.title}`;
  }
  
  if (lecturerNameEl) {
    lecturerNameEl.textContent = `Host: ${session.host.display_name}`;
  }
  
  if (studentCountEl) {
    const count = session.participant_count || 0;
    studentCountEl.textContent = `${count} Student${count !== 1 ? 's' : ''} Online`;
  }
}

/**
 * Populate the lecturer participant card with session creator's name
 */
function populateLecturerCard(session) {
  const lecturerCard = document.querySelector('.participant-card.lecturer .user-name');
  
  if (lecturerCard) {
    lecturerCard.textContent = `${session.host.display_name} (Creator)`;
  }
}

// New
document.addEventListener('DOMContentLoaded', () => {
    // 1. DOM Elements and Constants
    const postButton = document.querySelector('.post-button');
    const questionInput = document.querySelector('.input-area input[type="text"]');
    const discussionList = document.querySelector('.discussion-list');
    
    // Cloning the template for the empty state message
    const emptyFeedTemplate = document.querySelector('.empty-feed');
    const emptyFeed = emptyFeedTemplate ? emptyFeedTemplate.cloneNode(true) : null;
    
    const anonToggle = document.querySelector('.switch input[type="checkbox"]');
    
    const STORAGE_KEY = 'jcu_interactive_questions';
    const knownUserName = "Current User Name"; 
    const NEW_QUESTION_CUTOFF_MS = 5 * 60 * 1000; 

    // Critical Check: If the core elements are missing, stop execution silently.
    if (!postButton || !questionInput || !discussionList) {
        return;
    }

    // --- Initialization ---
    loadQuestions();
    
    // 2. Event Listeners (Delegated & Direct)
    postButton.addEventListener('click', handlePostQuestion);
    
    // Event Delegation for all actions within the discussion list (Vote, Reply Post, Toggles)
    discussionList.addEventListener('click', (e) => {
        // Prevent default action for link clicks
        e.preventDefault(); 
        
        // 1. Check for VOTE action (Highest priority)
        const voteAction = e.target.closest('.vote-action');
        if (voteAction && !e.target.closest('.card-footer')) {
            handleVote(e, voteAction);
            return; 
        }

        // 2. Check for REPLY SUBMISSION button click
        const replyPostButton = e.target.closest('.reply-post-button');
        if (replyPostButton) {
            handlePostReply(e);
            return;
        }

        // 3. Check for SHOW/HIDE Replies TOGGLE click (The count link)
        const repliesToggle = e.target.closest('.replies-toggle'); 
        if (repliesToggle) {
            handleRepliesToggle(e);
            return;
        }

        // 4. Check for REPLY INPUT BOX TOGGLE click (The "Reply" text link)
        const replyToggleLink = e.target.closest('.reply-action');
        if (replyToggleLink) {
            handleReplyToggle(e);
            return;
        }
    });

    // =======================================================
    // --- CORE LOGIC FUNCTIONS ---
    // =======================================================
    
    function handlePostQuestion() {
        const questionText = questionInput.value.trim();

        if (questionText) {
            const isAnonymous = anonToggle.checked;
            const author = isAnonymous ? "Anonymous" : knownUserName;
            
            const newQuestion = {
                id: Date.now() + Math.random(), 
                author: author,
                text: questionText,
                timestamp: Date.now(), 
                isAnswered: false, 
                votes: 0,
                replies: [] 
            };
            
            const questions = getStoredQuestions();
            questions.unshift(newQuestion); 
            saveQuestions(questions);

            renderQuestions(questions);

            questionInput.value = '';
            anonToggle.checked = false;
        } else {
            questionInput.placeholder = "Please type your question here!";
            questionInput.focus();
        }
    }

    // --- Vote/Like Logic ---

    function handleVote(e, voteActionElement) {
        e.preventDefault(); 

        const questionCard = voteActionElement.closest('.question-card');
        const questionId = parseFloat(questionCard.getAttribute('data-id'));
        
        let questions = getStoredQuestions();
        const qIndex = questions.findIndex(q => q.id === questionId);
        
        if (qIndex === -1) return;

        let question = questions[qIndex];
        const countSpan = voteActionElement.querySelector('.count'); 
        
        if (!countSpan) return;

        const hasVoted = voteActionElement.classList.contains('voted');

        if (hasVoted) {
            question.votes -= 1;
            voteActionElement.classList.remove('voted');
            
        } else {
            question.votes += 1;
            voteActionElement.classList.add('voted');
        }
        
        countSpan.textContent = question.votes;
        saveQuestions(questions);
    }
    
    // --- Reply Input Toggle Logic ---
    
    function handleReplyToggle(e) {
        e.preventDefault();
        e.stopPropagation();

        const card = e.target.closest('.question-card');
        if (card) {
            const inputWrapper = card.querySelector('.reply-input-wrapper');
            if (inputWrapper) {
                const isHidden = inputWrapper.style.display === 'none' || inputWrapper.style.display === '';
                inputWrapper.style.display = isHidden ? 'flex' : 'none';
                
                if (isHidden) {
                    inputWrapper.querySelector('input').focus();
                }
            }
        }
    }

    // --- Reply Post Logic ---
    
    function handlePostReply(e) {
        e.preventDefault(); 
        e.stopPropagation(); 

        const questionCard = e.target.closest('.question-card');
        if (!questionCard) return;

        const questionId = parseFloat(questionCard.getAttribute('data-id'));
        
        const inputWrapper = e.target.closest('.reply-input-wrapper');
        const replyInput = inputWrapper.querySelector('.reply-input');
        const repliesContainer = questionCard.querySelector('.replies-container');
        const replyText = replyInput.value.trim();

        if (replyText && repliesContainer) {
            
            const newReply = {
                author: knownUserName,
                text: replyText,
                timestamp: Date.now(),
                isApproved: false,
            };
            
            let questions = getStoredQuestions();
            const qIndex = questions.findIndex(q => q.id === questionId);
            
            if (qIndex !== -1) {
                questions[qIndex].replies.unshift(newReply); 
                saveQuestions(questions);
                
                const newReplyHtml = createReplyHtml(newReply);
                repliesContainer.insertAdjacentHTML('afterbegin', newReplyHtml);

                const currentCount = questions[qIndex].replies.length;
                updateReplyCount(questionCard, currentCount);

                inputWrapper.style.display = 'none';
                replyInput.value = '';
            }
        }
    }
    
    // --- Replies Container Toggle Logic ---
    
    function handleRepliesToggle(e) {
        const toggleElement = e.target.closest('.replies-toggle');
        if (!toggleElement) return;
        
        const card = toggleElement.closest('.question-card');
        const repliesContainer = card.querySelector('.replies-container');
        
        const questionId = parseFloat(card.getAttribute('data-id'));
        const questions = getStoredQuestions();
        const question = questions.find(q => q.id === questionId);
        
        if (!question || question.replies.length === 0) return;

        const isOpen = repliesContainer.classList.contains('open');

        if (isOpen) {
            repliesContainer.classList.remove('open');
            toggleElement.setAttribute('data-replies-open', 'false');
        } else {
            repliesContainer.classList.add('open');
            toggleElement.setAttribute('data-replies-open', 'true');
        }
    }

    // =======================================================
    // --- RENDERING & HELPER FUNCTIONS ---
    // =======================================================
    
    function renderQuestions(questions) {
        discussionList.innerHTML = ''; 

        if (questions.length === 0) {
            if (emptyFeed) {
                discussionList.appendChild(emptyFeed);
                emptyFeed.style.display = 'flex';
            }
        } else {
            questions.forEach(question => {
                const cardHTML = createQuestionCard(question);
                discussionList.insertAdjacentHTML('beforeend', cardHTML);
            });
        }
    }
    
    function getStoredQuestions() {
        // ... (Your implementation remains the same)
        const stored = localStorage.getItem(STORAGE_KEY);
        try {
            const questions = stored ? JSON.parse(stored) : [];
            return questions.map(q => {
                let id = parseFloat(q.id);
                if (isNaN(id)) {
                    id = Date.now() + Math.random(); 
                }
                return {
                    ...q,
                    id: id,
                    replies: q.replies || [] 
                };
            });
        } catch (e) {
            console.error("Error parsing questions from Local Storage:", e);
            return [];
        }
    }
    
    function saveQuestions(questions) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(questions));
    }
    
    function loadQuestions() {
        const questions = getStoredQuestions();
        renderQuestions(questions);
    }
    
    function updateReplyCount(cardElement, count) {
        const replyCountSpan = cardElement.querySelector('.card-footer .footer-right span:first-child');
        if (replyCountSpan) {
            const arrowIcon = count > 0 ? 'keyboard_arrow_up' : 'keyboard_arrow_down';
            replyCountSpan.innerHTML = `Show Reply (${count}) <span class="material-symbols-outlined icon-sm">${arrowIcon}</span>`;
        }
    }
    
    function isQuestionNew(timestamp) {
        const ageMs = Date.now() - timestamp; 
        return ageMs < NEW_QUESTION_CUTOFF_MS;
    }

    function getQuestionTag(question) {
        if (question.isAnswered) {
             return { text: "ANSWERED", className: "tag-answered" };
        }
        if (isQuestionNew(question.timestamp)) {
            return { text: "NEW", className: "tag-new" };
        } else {
            return { text: "OLD", className: "tag-old" };
        }
    }

    function formatTimestamp(ms) {
        const seconds = Math.floor((Date.now() - ms) / 1000);
        if (seconds < 5) return 'just now';
        if (seconds < 60) return `${seconds} secs ago`;
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes} mins ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} hours ago`;
        return new Date(ms).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    }

    function createReplyHtml(reply) {
        const displayTime = formatTimestamp(reply.timestamp);
        let tagHtml = '';
        if (reply.isApproved) {
            tagHtml = `<span class="tag tag-approved">APPROVED ANSWER</span>`;
        }
        
        return `
            <div class="nested-reply-wrapper">
                <div class="nested-reply">
                    <div class="card-header">
                        <div class="author-row">
                            <span class="author-name">${reply.author}</span>
                            ${tagHtml}
                        </div>
                    </div>
                    <div class="timestamp">${displayTime}</div>
                    <div class="reply-text">
                        ${reply.text}
                    </div>
                </div>
            </div>
        `;
    }

    function createQuestionCard(question) {
        const displayTime = formatTimestamp(question.timestamp);
        const tag = getQuestionTag(question); 
        const dataId = question.id; 
        
        const votedClass = ''; 
        const iconSymbol = 'thumb_up'; 
        
        let repliesHtml = '';
        if (question.replies && question.replies.length > 0) {
            repliesHtml = [...question.replies].reverse().map(createReplyHtml).join('');
        }

        const replyInputHtml = `
            <div class="reply-input-wrapper" style="display: none;">
                <input type="text" placeholder="Add a reply..." class="reply-input">
                <button class="reply-post-button" data-question-id="${dataId}">Post</button>
            </div>
        `;
        
        const repliesExist = question.replies.length > 0;
        const toggleState = 'false'; 
        const arrowIcon = repliesExist ? 'keyboard_arrow_up' : 'keyboard_arrow_down';
        // Note: The toggle state starts closed. The replies container needs the 'open' class only if the user clicks it.

        return `
            <div class="question-card" data-id="${dataId}">
              <div class="card-header">
                <div class="author-row">
                  <span class="author-name">${question.author}</span>
                  <span class="tag ${tag.className}">${tag.text}</span>
                </div>
                <div class="vote-action ${votedClass}">
                  <span class="material-symbols-outlined vote-icon">${iconSymbol}</span>
                  <span class="count">${question.votes}</span>
                </div>
              </div>
              <div class="timestamp">${displayTime}</div>
              
              <div class="question-bubble">
                ${question.text}
              </div>
              
              <div class="card-footer">
                <div class="footer-left">
                  <span class="reply-action action-link"><span class="material-symbols-outlined icon-sm">reply</span> Reply</span>
                </div>
                <div class="footer-right replies-toggle" data-replies-open="${toggleState}">
                  <span class="action-link">Show Reply (${question.replies.length}) <span class="material-symbols-outlined icon-sm">${arrowIcon}</span></span>
                </div>
              </div>
              ${replyInputHtml}
              <div class="replies-container">
                  ${repliesHtml}
              </div>
            </div>
        `;
    }
});
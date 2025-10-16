/**
 * Utility Functions
 * 
 * Pure helper functions with no side effects.
 * Reusable across different parts of the application.
 */

/**
 * Escape HTML special characters to prevent XSS attacks.
 * 
 * ALWAYS use this function when inserting user-provided content into innerHTML.
 * 
 * @param {string} text - The text to escape
 * @returns {string} HTML-safe string with special chars escaped
 * 
 * @example
 * escapeHtml('<img src=x onerror=alert(1)>')
 * // returns: '&lt;img src=x onerror=alert(1)&gt;'
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

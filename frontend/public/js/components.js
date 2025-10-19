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

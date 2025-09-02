/**
 * API helper for backend communication
 */

// Get API base URL from environment or use empty string for proxy
const API_BASE = process.env.REACT_APP_API_BASE || '';

/**
 * Process a PDF document with keyword filtering
 * @param {string} keyword - Keyword to search for
 * @param {File} file - PDF file to process
 * @returns {Promise<Object>} API response
 */
export async function processDocument(keyword, file) {
  // Build form data
  const formData = new FormData();
  formData.append('keyword', keyword);
  formData.append('file', file);

  // Make API request
  const response = await fetch(`${API_BASE}/api/process-document`, {
    method: 'POST',
    body: formData
  });

  // Parse response
  const data = await response.json();

  // Check for errors
  if (!response.ok) {
    throw new Error(data.error?.message || `HTTP error! status: ${response.status}`);
  }

  return data;
}

/**
 * Extract PGX gene data from a PDF document
 * @param {string} keyword - Keyword that appears only in PGX table pages
 * @param {File} file - PDF file to process
 * @returns {Promise<Object>} API response with extracted gene data
 */
export async function extractPgxData(keyword, file) {
  // Build form data
  const formData = new FormData();
  formData.append('keyword', keyword);
  formData.append('file', file);

  // Make API request
  const response = await fetch(`${API_BASE}/api/extract-pgx-data`, {
    method: 'POST',
    body: formData
  });

  // Parse response
  const data = await response.json();

  // Check for errors
  if (!response.ok) {
    throw new Error(data.error?.message || `HTTP error! status: ${response.status}`);
  }

  return data;
}
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

/**
 * Handles API responses, raising clear errors if HTTP status is not OK.
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Fallback if response is not JSON
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

/**
 * Fetches all engineering issues from backend with optional filtering.
 */
export async function fetchIssues(statusFilter = '', priorityFilter = '') {
  const params = new URLSearchParams();
  if (statusFilter && statusFilter !== 'all') params.append('status', statusFilter);
  if (priorityFilter && priorityFilter !== 'all') params.append('priority', priorityFilter);

  const queryString = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE_URL}/issues${queryString}`);
  return handleResponse(response);
}

/**
 * Fetches a single issue by primary key ID.
 */
export async function fetchIssueById(id) {
  const response = await fetch(`${API_BASE_URL}/issues/${id}`);
  return handleResponse(response);
}

/**
 * Submits a new issue to POST /api/v1/issues.
 */
export async function createIssue(issueData) {
  const response = await fetch(`${API_BASE_URL}/issues`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(issueData),
  });
  return handleResponse(response);
}

/**
 * Updates an issue via PUT /api/v1/issues/{id}.
 */
export async function updateIssue(id, issueData) {
  const response = await fetch(`${API_BASE_URL}/issues/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(issueData),
  });
  return handleResponse(response);
}

/**
 * Deletes an issue via DELETE /api/v1/issues/{id}.
 */
export async function deleteIssue(id) {
  const response = await fetch(`${API_BASE_URL}/issues/${id}`, {
    method: 'DELETE',
  });
  return handleResponse(response);
}

import React from 'react';
import StatusBadge from './StatusBadge';
import PriorityBadge from './PriorityBadge';

export default function IssueTable({ issues, loading, error, onSelectIssue, onDeleteIssue }) {
  if (loading) {
    return (
      <div className="table-container state-box">
        <div className="spinner"></div>
        <p>Loading issues from FastAPI backend...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="table-container state-box error-box">
        <h3>Unable to load issues</h3>
        <p className="error-text">{error}</p>
        <p className="subtext">Ensure FastAPI server is running on port 8000 and PostgreSQL is accessible.</p>
      </div>
    );
  }

  if (!issues || issues.length === 0) {
    return (
      <div className="table-container state-box empty-box">
        <h3>No Issues Found</h3>
        <p>No engineering tickets match your criteria. Create a new issue to get started.</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="issue-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title & Description</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Team</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {issues.map((issue) => (
            <tr key={issue.id} className="table-row">
              <td className="cell-id">#{issue.id}</td>
              <td className="cell-main">
                <div className="issue-title" onClick={() => onSelectIssue(issue)}>
                  {issue.title}
                </div>
                {issue.description && (
                  <div className="issue-desc">
                    {issue.description.length > 85
                      ? `${issue.description.substring(0, 85)}...`
                      : issue.description}
                  </div>
                )}
              </td>
              <td>
                <span className="category-tag">{issue.category}</span>
              </td>
              <td>
                <PriorityBadge priority={issue.priority} />
              </td>
              <td>
                <StatusBadge status={issue.status} />
              </td>
              <td>
                <span className="team-tag">{issue.assigned_team || 'Unassigned'}</span>
              </td>
              <td className="cell-date">
                {issue.created_at ? new Date(issue.created_at).toLocaleDateString() : 'N/A'}
              </td>
              <td className="cell-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => onSelectIssue(issue)}
                >
                  View / Edit
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => onDeleteIssue(issue.id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

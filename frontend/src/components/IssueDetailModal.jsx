import React, { useState, useEffect } from 'react';
import { updateIssue, deleteIssue } from '../services/api';
import StatusBadge from './StatusBadge';
import PriorityBadge from './PriorityBadge';

export default function IssueDetailModal({ issue, isOpen, onClose, onSuccess, onDeleteSuccess }) {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (issue) {
      setFormData({
        title: issue.title || '',
        description: issue.description || '',
        category: issue.category || 'bug',
        priority: issue.priority || 'medium',
        status: issue.status || 'open',
        assigned_team: issue.assigned_team || 'backend',
      });
      setIsEditing(false);
      setError(null);
    }
  }, [issue]);

  if (!isOpen || !issue) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await updateIssue(issue.id, formData);
      setSubmitting(false);
      setIsEditing(false);
      onSuccess();
    } catch (err) {
      setSubmitting(false);
      setError(err.message || 'Failed to update issue');
    }
  };

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete Issue #${issue.id} ("${issue.title}")?`)) {
      setSubmitting(true);
      try {
        await deleteIssue(issue.id);
        setSubmitting(false);
        onDeleteSuccess();
        onClose();
      } catch (err) {
        setSubmitting(false);
        setError(err.message || 'Failed to delete issue');
      }
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container">
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="issue-id-tag">#{issue.id}</span>
            <h2>{isEditing ? 'Edit Issue Details' : issue.title}</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {!isEditing ? (
          <div className="modal-body">
            <div className="detail-meta-bar">
              <div className="meta-item">
                <span className="meta-label">Status:</span>
                <StatusBadge status={issue.status} />
              </div>
              <div className="meta-item">
                <span className="meta-label">Priority:</span>
                <PriorityBadge priority={issue.priority} />
              </div>
              <div className="meta-item">
                <span className="meta-label">Category:</span>
                <span className="category-tag">{issue.category}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Team:</span>
                <span className="team-tag">{issue.assigned_team || 'Unassigned'}</span>
              </div>
            </div>

            <div className="detail-section">
              <h3>Description</h3>
              <div className="detail-description-box">
                {issue.description || <em>No detailed description provided.</em>}
              </div>
            </div>

            <div className="detail-timestamps">
              <div>Created: {issue.created_at ? new Date(issue.created_at).toLocaleString() : 'N/A'}</div>
              <div>Updated: {issue.updated_at ? new Date(issue.updated_at).toLocaleString() : 'N/A'}</div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleDelete}
                disabled={submitting}
              >
                Delete Issue
              </button>
              <div className="footer-right-buttons">
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                  Close
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setIsEditing(true)}
                >
                  Edit Issue
                </button>
              </div>
            </div>
          </div>
        ) : (
          <form onSubmit={handleUpdateSubmit} className="modal-body">
            <div className="form-group">
              <label className="form-label">Title *</label>
              <input
                type="text"
                name="title"
                className="form-input"
                value={formData.title}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea
                name="description"
                className="form-textarea"
                rows="4"
                value={formData.description}
                onChange={handleChange}
              ></textarea>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  name="category"
                  className="form-select"
                  value={formData.category}
                  onChange={handleChange}
                >
                  <option value="bug">Bug</option>
                  <option value="feature">Feature</option>
                  <option value="incident">Incident</option>
                  <option value="task">Task</option>
                  <option value="tech_debt">Tech Debt</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Priority</label>
                <select
                  name="priority"
                  className="form-select"
                  value={formData.priority}
                  onChange={handleChange}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Status</label>
                <select
                  name="status"
                  className="form-select"
                  value={formData.status}
                  onChange={handleChange}
                >
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Assigned Team</label>
                <select
                  name="assigned_team"
                  className="form-select"
                  value={formData.assigned_team}
                  onChange={handleChange}
                >
                  <option value="backend">Backend</option>
                  <option value="frontend">Frontend</option>
                  <option value="devops">DevOps</option>
                  <option value="platform">Platform</option>
                  <option value="data">Data Engineering</option>
                </select>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setIsEditing(false)}
                disabled={submitting}
              >
                Cancel Edit
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

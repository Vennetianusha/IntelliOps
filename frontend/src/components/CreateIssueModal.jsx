import React, { useState } from 'react';
import { createIssue, analyzeIssue } from '../services/api';
import PriorityBadge from './PriorityBadge';

export default function CreateIssueModal({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'bug',
    priority: 'medium',
    status: 'open',
    assigned_team: '',
  });

  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiError, setAiError] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleAnalyzeWithAI = async () => {
    if (!formData.title.trim()) {
      setError('Please enter an issue title before analyzing with AI.');
      return;
    }

    setAnalyzing(true);
    setAiError(null);
    setError(null);

    try {
      const result = await analyzeIssue(formData.title, formData.description);
      setAiAnalysis(result);
      setAnalyzing(false);

      // Auto-populate Category, Priority, Assigned Team from AI response
      setFormData((prev) => ({
        ...prev,
        category: result.category || prev.category,
        priority: result.priority || prev.priority,
        assigned_team: result.assigned_team || prev.assigned_team,
      }));
    } catch (err) {
      setAnalyzing(false);
      setAiError('AI analysis unavailable. You can still create the issue manually.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }
    if (!formData.category.trim()) {
      setError('Category is required');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await createIssue(formData);
      setSubmitting(false);
      // Reset form and states
      setFormData({
        title: '',
        description: '',
        category: 'bug',
        priority: 'medium',
        status: 'open',
        assigned_team: '',
      });
      setAiAnalysis(null);
      setAiError(null);
      onSuccess();
      onClose();
    } catch (err) {
      setSubmitting(false);
      setError(err.message || 'Failed to create issue');
    }
  };

  const handleCloseModal = () => {
    setAiAnalysis(null);
    setAiError(null);
    setError(null);
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container modal-lg">
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-badge-ai">🤖 AI Triage</span>
            <h2>Create New Engineering Issue</h2>
          </div>
          <button className="modal-close-btn" onClick={handleCloseModal}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">Title *</label>
            <input
              type="text"
              name="title"
              className="form-input"
              placeholder="e.g. Database connection pool exhaustion during high traffic load"
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
              rows="3"
              placeholder="Provide technical details, steps to reproduce, or error logs..."
              value={formData.description}
              onChange={handleChange}
            ></textarea>
          </div>

          {/* AI Trigger Bar */}
          <div className="ai-trigger-bar" style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <button
              type="button"
              className="btn btn-ai-analyze"
              onClick={handleAnalyzeWithAI}
              disabled={analyzing || !formData.title.trim()}
            >
              {analyzing ? (
                <>
                  <span className="mini-spinner"></span>
                  Analyzing issue...
                </>
              ) : (
                '🤖 Analyze with AI'
              )}
            </button>
          </div>

          {/* AI Error Warning */}
          {aiError && (
            <div className="alert alert-warning ai-alert">
              <span>⚠️ {aiError}</span>
            </div>
          )}

          {/* AI Analysis Result Card */}
          {aiAnalysis && (
            <div className="ai-analysis-card">
              <div className="ai-card-header">
                <div className="ai-card-title">
                  <span className="ai-icon">🤖</span>
                  <h3>AI Analysis</h3>
                </div>
                <span className="ai-card-subtitle">Auto-filled into form below</span>
              </div>

              <div className="ai-card-body">
                <div className="ai-meta-grid">
                  <div className="ai-meta-item">
                    <span className="ai-meta-label">Category</span>
                    <span className="category-tag bold">{aiAnalysis.category}</span>
                  </div>
                  <div className="ai-meta-item">
                    <span className="ai-meta-label">Priority</span>
                    <PriorityBadge priority={aiAnalysis.priority} />
                  </div>
                  <div className="ai-meta-item">
                    <span className="ai-meta-label">Assigned Team</span>
                    <span className="team-tag bold">{aiAnalysis.assigned_team}</span>
                  </div>
                </div>

                {aiAnalysis.keywords && aiAnalysis.keywords.length > 0 && (
                  <div className="ai-keywords-group">
                    <span className="ai-meta-label">Keywords</span>
                    <div className="keywords-flex">
                      {aiAnalysis.keywords.map((kw, i) => (
                        <span key={i} className="keyword-chip">
                          #{kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {aiAnalysis.suggested_action && (
                  <div className="ai-action-box">
                    <span className="ai-meta-label">Suggested Action</span>
                    <p className="ai-action-text">{aiAnalysis.suggested_action}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* User Fields (Auto-populated from AI, but editable) */}
          <div className="form-section-title">
            <span>Ticket Parameters & Review</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Category *</label>
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
              onClick={handleCloseModal}
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving to PostgreSQL...' : 'Create Issue'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


import React from 'react';
import StatusBadge from './StatusBadge';
import PriorityBadge from './PriorityBadge';

/**
 * Returns a standard suggested action based on stored category and assigned team.
 */
function getActionSuggestion(category, team, priority) {
  const cat = (category || 'bug').toLowerCase();
  const tm = (team || 'backend').toLowerCase();
  const pri = (priority || 'medium').toLowerCase();

  if (cat === 'incident' || pri === 'critical') {
    return `Immediate investigation by ${tm} team. Check system logs and alert on-call engineer.`;
  }
  if (cat === 'bug') {
    return `Reproduce in dev environment, inspect stack trace, and assign to ${tm} sprint.`;
  }
  if (cat === 'feature') {
    return `Review technical requirements with product lead and assign design review to ${tm}.`;
  }
  if (cat === 'tech_debt') {
    return `Audit target code area in ${tm} repository and schedule refactoring task.`;
  }
  return `Review ticket details, assign ${tm} engineer, and estimate story points.`;
}

export default function AiInsightsSection({ issues = [], onSelectIssue }) {
  // Take up to 4 recent issues
  const recentIssues = issues.slice(0, 4);

  if (issues.length === 0) {
    return (
      <section className="ai-insights-container">
        <div className="insights-header">
          <div className="insights-title">
            <span className="ai-sparkle">🤖</span>
            <h3>AI Engineering Insights</h3>
          </div>
          <span className="insights-badge">Live System Data</span>
        </div>
        <div className="insights-empty">
          <p>No active issues found in PostgreSQL database.</p>
          <span className="subtext">Create an issue with AI analysis to see operational recommendations here.</span>
        </div>
      </section>
    );
  }

  return (
    <section className="ai-insights-container">
      <div className="insights-header">
        <div className="insights-title">
          <span className="ai-sparkle">🤖</span>
          <h3>AI Engineering Insights</h3>
        </div>
        <span className="insights-badge">{recentIssues.length} Recent Tickets Analyzed</span>
      </div>

      <div className="insights-grid">
        {recentIssues.map((issue) => {
          const actionText = getActionSuggestion(issue.category, issue.assigned_team, issue.priority);

          return (
            <div
              key={issue.id}
              className={`insight-card priority-${issue.priority || 'medium'}`}
              onClick={() => onSelectIssue && onSelectIssue(issue)}
            >
              <div className="insight-card-top">
                <span className="insight-id">#{issue.id}</span>
                <StatusBadge status={issue.status} />
              </div>

              <h4 className="insight-card-title">{issue.title}</h4>

              <div className="insight-tags">
                <span className="category-tag">{issue.category || 'bug'}</span>
                <PriorityBadge priority={issue.priority} />
                <span className="team-tag">{issue.assigned_team || 'Unassigned'}</span>
              </div>

              <div className="insight-action-box">
                <span className="action-label">🤖 Suggested Action:</span>
                <p className="action-text">{actionText}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

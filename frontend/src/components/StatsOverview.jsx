import React from 'react';

export default function StatsOverview({ issues = [] }) {
  const total = issues.length;
  const openCount = issues.filter((i) => i.status === 'open').length;
  const inProgressCount = issues.filter((i) => i.status === 'in_progress').length;
  const resolvedCount = issues.filter((i) => i.status === 'resolved' || i.status === 'closed').length;
  const criticalCount = issues.filter((i) => i.priority === 'critical' || i.priority === 'high').length;

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Total Issues</div>
        <div className="stat-value">{total}</div>
        <div className="stat-desc">Tracked in PostgreSQL</div>
      </div>

      <div className="stat-card border-blue">
        <div className="stat-label">Open Issues</div>
        <div className="stat-value text-blue">{openCount}</div>
        <div className="stat-desc">Awaiting resolution</div>
      </div>

      <div className="stat-card border-yellow">
        <div className="stat-label">In Progress</div>
        <div className="stat-value text-yellow">{inProgressCount}</div>
        <div className="stat-desc">Active dev tickets</div>
      </div>

      <div className="stat-card border-green">
        <div className="stat-label">Resolved / Closed</div>
        <div className="stat-value text-green">{resolvedCount}</div>
        <div className="stat-desc">Successfully completed</div>
      </div>

      <div className="stat-card border-red">
        <div className="stat-label">Critical & High</div>
        <div className="stat-value text-red">{criticalCount}</div>
        <div className="stat-desc">Urgent priority tickets</div>
      </div>
    </div>
  );
}

import React from 'react';

const PRIORITY_CONFIG = {
  low: { label: 'Low', className: 'badge-priority-low' },
  medium: { label: 'Medium', className: 'badge-priority-medium' },
  high: { label: 'High', className: 'badge-priority-high' },
  critical: { label: 'Critical', className: 'badge-priority-critical' },
};

export default function PriorityBadge({ priority }) {
  const config = PRIORITY_CONFIG[priority] || { label: priority, className: 'badge-priority-medium' };
  return <span className={`badge ${config.className}`}>{config.label}</span>;
}

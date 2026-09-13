import React from 'react';

const STATUS_CONFIG = {
  open: { label: 'Open', className: 'badge-status-open' },
  in_progress: { label: 'In Progress', className: 'badge-status-progress' },
  resolved: { label: 'Resolved', className: 'badge-status-resolved' },
  closed: { label: 'Closed', className: 'badge-status-closed' },
};

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || { label: status, className: 'badge-status-closed' };
  return <span className={`badge ${config.className}`}>{config.label}</span>;
}

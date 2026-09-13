import React from 'react';

export default function IssueFilters({
  statusFilter,
  setStatusFilter,
  priorityFilter,
  setPriorityFilter,
  searchQuery,
  setSearchQuery,
  onReset,
}) {
  return (
    <div className="filter-bar">
      <div className="search-input-wrapper">
        <input
          type="text"
          className="form-input search-input"
          placeholder="Filter by title, description, or team..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="filter-dropdowns">
        <div className="filter-group">
          <label>Status:</label>
          <select
            className="form-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Priority:</label>
          <select
            className="form-select"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="all">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        {(statusFilter !== 'all' || priorityFilter !== 'all' || searchQuery) && (
          <button className="btn btn-secondary btn-sm" onClick={onReset}>
            Reset Filters
          </button>
        )}
      </div>
    </div>
  );
}

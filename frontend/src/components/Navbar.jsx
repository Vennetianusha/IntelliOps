import React from 'react';

export default function Navbar({ activeTab, setActiveTab, onOpenCreateModal, apiOnline }) {
  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <div className="logo-icon">IO</div>
          <div className="brand-text">
            <span className="brand-name">IntelliOps</span>
            <span className="brand-sub">Engineering Operations</span>
          </div>
        </div>

        <nav className="navbar-links">
          <button
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={`nav-btn ${activeTab === 'issues' ? 'active' : ''}`}
            onClick={() => setActiveTab('issues')}
          >
            All Issues
          </button>
        </nav>

        <div className="navbar-actions">
          <div className={`api-indicator ${apiOnline ? 'online' : 'offline'}`}>
            <span className="dot"></span>
            <span>{apiOnline ? 'FastAPI Online' : 'Backend Disconnected'}</span>
          </div>
          <button className="btn btn-primary" onClick={onOpenCreateModal}>
            + Create Issue
          </button>
        </div>
      </div>
    </header>
  );
}

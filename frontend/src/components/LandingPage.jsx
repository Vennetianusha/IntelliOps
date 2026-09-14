import React from 'react';

export default function LandingPage({ onOpenDashboard }) {
  return (
    <div className="landing-container">
      <section className="landing-hero">
        <div className="hero-logo">
          <span className="gradient-text">IntelliOps</span>
        </div>

        <h1 className="hero-title">
          AI-Powered Engineering Issue Management
        </h1>

        <p className="hero-subtitle">
          Create, analyze, prioritize, and manage engineering issues with AI-assisted triage.
        </p>

        <div className="hero-cta-group">
          <button className="btn btn-hero-primary" onClick={onOpenDashboard}>
            Open IntelliOps Dashboard →
          </button>
        </div>
      </section>
    </div>
  );
}


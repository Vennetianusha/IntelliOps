import { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import LandingPage from './components/LandingPage';
import StatsOverview from './components/StatsOverview';
import AiInsightsSection from './components/AiInsightsSection';
import IssueFilters from './components/IssueFilters';
import IssueTable from './components/IssueTable';
import CreateIssueModal from './components/CreateIssueModal';
import IssueDetailModal from './components/IssueDetailModal';
import { fetchIssues, deleteIssue } from './services/api';

export default function App() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);

  // Default view is 'landing' as required by prompt
  const [activeTab, setActiveTab] = useState('landing');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedIssue, setSelectedIssue] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch API Health & Issues
  const loadIssues = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const healthRes = await fetch('/api/v1/health').catch(() => null);
      if (healthRes && healthRes.ok) {
        setApiOnline(true);
      } else {
        setApiOnline(false);
      }

      const data = await fetchIssues(statusFilter, priorityFilter);
      setIssues(data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      setError(err.message || 'Failed to connect to backend service.');
    }
  }, [statusFilter, priorityFilter]);

  useEffect(() => {
    loadIssues();
  }, [loadIssues]);

  const handleResetFilters = () => {
    setStatusFilter('all');
    setPriorityFilter('all');
    setSearchQuery('');
  };

  // Filter issues locally by search query
  const filteredIssues = issues.filter((issue) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    const titleMatch = issue.title?.toLowerCase().includes(query);
    const descMatch = issue.description?.toLowerCase().includes(query);
    const teamMatch = issue.assigned_team?.toLowerCase().includes(query);
    const categoryMatch = issue.category?.toLowerCase().includes(query);
    return titleMatch || descMatch || teamMatch || categoryMatch;
  });

  return (
    <div className="app-wrapper">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
        apiOnline={apiOnline}
      />

      {activeTab === 'landing' ? (
        <LandingPage onOpenDashboard={() => setActiveTab('dashboard')} />
      ) : (
        <main className="container">
          {activeTab === 'dashboard' && (
            <>
              <section className="section-dashboard">
                <div className="section-header-flex">
                  <div>
                    <h2>Operations Overview</h2>
                    <p className="section-subtext">Real-time status from PostgreSQL & Redis cache</p>
                  </div>
                  <button className="btn btn-primary" onClick={() => setIsCreateModalOpen(true)}>
                    <span>+</span> Create Issue
                  </button>
                </div>
                <StatsOverview issues={issues} />
              </section>

              <AiInsightsSection
                issues={issues}
                onSelectIssue={(issue) => setSelectedIssue(issue)}
              />
            </>
          )}

          <section className="section-issues">
            <div className="section-header-flex" style={{ marginBottom: '1rem' }}>
              <div>
                <h2>Engineering Issues</h2>
                <p className="section-subtext">Manage, filter, and triage active tickets</p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={loadIssues}>
                🔄 Refresh List
              </button>
            </div>

            <IssueFilters
              statusFilter={statusFilter}
              setStatusFilter={setStatusFilter}
              priorityFilter={priorityFilter}
              setPriorityFilter={setPriorityFilter}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              onReset={handleResetFilters}
            />

            <IssueTable
              issues={filteredIssues}
              loading={loading}
              error={error}
              onSelectIssue={(issue) => setSelectedIssue(issue)}
              onDeleteIssue={async (id) => {
                if (window.confirm(`Delete issue #${id}?`)) {
                  try {
                    await deleteIssue(id);
                    loadIssues();
                  } catch (err) {
                    alert(`Failed to delete issue: ${err.message}`);
                  }
                }
              }}
            />
          </section>
        </main>
      )}

      <CreateIssueModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={loadIssues}
      />

      <IssueDetailModal
        issue={selectedIssue}
        isOpen={!!selectedIssue}
        onClose={() => setSelectedIssue(null)}
        onSuccess={loadIssues}
        onDeleteSuccess={loadIssues}
      />

      <footer className="footer">
        IntelliOps &copy; 2026 – AI-Powered Engineering Operations Platform
      </footer>
    </div>
  );
}

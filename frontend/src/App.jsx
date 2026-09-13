import { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import StatsOverview from './components/StatsOverview';
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

  // Tabs & Modal state
  const [activeTab, setActiveTab] = useState('dashboard');
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
      // Health check endpoint
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
    return titleMatch || descMatch || teamMatch;
  });

  return (
    <div className="app-wrapper">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
        apiOnline={apiOnline}
      />

      <main className="container">
        {activeTab === 'dashboard' && (
          <section className="section-dashboard">
            <h2 style={{ marginBottom: '1rem' }}>Operations Overview</h2>
            <StatsOverview issues={issues} />
          </section>
        )}

        <section className="section-issues">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Engineering Issues</h2>
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

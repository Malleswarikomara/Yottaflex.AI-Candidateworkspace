import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import OverviewTab from './pages/OverviewTab';
import LogExplorerTab from './pages/LogExplorerTab';
import PerformanceTab from './pages/PerformanceTab';
import DataQualityTab from './pages/DataQualityTab';
import PipelineMonitoringTab from './pages/PipelineMonitoringTab';
import IngestionCenterTab from './pages/IngestionCenterTab';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [health, setHealth] = useState(false);
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchGlobalData = async () => {
    try {
      const [h, s, r] = await Promise.all([
        api.getHealth().then(() => true).catch(() => false),
        api.getStats().catch(() => null),
        api.getPipelineRuns(30).catch(() => []),
      ]);
      setHealth(h);
      setStats(s);
      setRuns(r || []);
    } catch (err) {
      console.error('Failed to load global data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGlobalData();
    const interval = setInterval(fetchGlobalData, 10000); // Polling every 10s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} health={health} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <OverviewTab stats={stats} runs={runs} onRefresh={fetchGlobalData} />
        )}
        {activeTab === 'logs' && <LogExplorerTab />}
        {activeTab === 'performance' && <PerformanceTab stats={stats} />}
        {activeTab === 'quality' && <DataQualityTab runs={runs} />}
        {activeTab === 'monitoring' && (
          <PipelineMonitoringTab runs={runs} onRefresh={fetchGlobalData} />
        )}
        {activeTab === 'ingestion' && (
          <IngestionCenterTab onPipelineSuccess={fetchGlobalData} />
        )}
      </main>

      <footer className="bg-slate-950 border-t border-slate-900 py-4 text-center text-xs text-slate-500 font-mono">
        Application Log Analytics & Monitoring Platform • Three-Tier Architecture (React.js + FastAPI + PostgreSQL/SQLite)
      </footer>
    </div>
  );
}

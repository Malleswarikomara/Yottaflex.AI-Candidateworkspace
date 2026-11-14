import React, { useState, useEffect } from 'react';
import { Search, Filter, ChevronLeft, ChevronRight, X, Eye, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function LogExplorerTab() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);

  // Filters
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('');
  const [service, setService] = useState('');
  const [onlyFailures, setOnlyFailures] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getLogs({
        page,
        limit,
        search,
        severity: severity || undefined,
        service: service || undefined,
        is_failure: onlyFailures ? true : undefined,
      });
      setLogs(data.items || []);
      setTotalRecords(data.total_records || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, limit, severity, service, onlyFailures]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'INFO':
        return 'bg-blue-950 text-blue-300 border-blue-800';
      case 'WARNING':
        return 'bg-amber-950 text-amber-300 border-amber-800';
      case 'ERROR':
        return 'bg-rose-950 text-rose-300 border-rose-800';
      case 'CRITICAL':
        return 'bg-red-950 text-red-200 border-red-700 font-bold';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const getLatencyColor = (ms) => {
    if (ms === null || ms === undefined) return 'text-slate-500';
    if (ms > 1000) return 'text-rose-400 font-bold';
    if (ms > 300) return 'text-amber-400';
    return 'text-emerald-400';
  };

  return (
    <div className="space-y-4">
      {/* Search and Filters Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by message, event ID, user ID, or endpoint..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition font-mono"
            />
          </div>

          {/* Severity Dropdown */}
          <select
            value={severity}
            onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="">All Severities</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>

          {/* Service Dropdown */}
          <select
            value={service}
            onChange={(e) => { setService(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="">All Services</option>
            <option value="auth">auth</option>
            <option value="payment">payment</option>
            <option value="api-gateway">api-gateway</option>
            <option value="order-service">order-service</option>
            <option value="inventory">inventory</option>
            <option value="notification">notification</option>
          </select>

          {/* Failures Only Toggle */}
          <label className="flex items-center space-x-2 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={onlyFailures}
              onChange={(e) => { setOnlyFailures(e.target.checked); setPage(1); }}
              className="rounded bg-slate-800 border-slate-700 text-indigo-500 focus:ring-0"
            />
            <span>Failures Only</span>
          </label>

          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition"
          >
            Search
          </button>
        </form>

        {/* Total Records Count Info */}
        <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
          <span>
            Showing <strong className="text-slate-200">{logs.length}</strong> of{' '}
            <strong className="text-slate-200">{totalRecords.toLocaleString()}</strong> matched logs
          </span>
          <div className="flex items-center space-x-2">
            <span>Per page:</span>
            <select
              value={limit}
              onChange={(e) => { setLimit(Number(e.target.value)); setPage(1); }}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-0.5 text-xs text-slate-300"
            >
              <option value="15">15</option>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Timestamp (UTC)</th>
                <th className="px-3 py-3">Severity</th>
                <th className="px-3 py-3">Service</th>
                <th className="px-3 py-3">Latency</th>
                <th className="px-3 py-3">User ID</th>
                <th className="px-4 py-3">Message</th>
                <th className="px-3 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-10 text-slate-500">
                    Loading logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-10 text-slate-500">
                    No matching log records found
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.event_id} className="hover:bg-slate-800/50 transition">
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-400">
                      {log.timestamp ? log.timestamp.replace('T', ' ').substring(0, 19) : '--'}
                    </td>
                    <td className="px-3 py-2.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded border text-[11px] font-semibold ${getSeverityBadge(log.severity)}`}>
                        {log.severity}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {log.service}
                      </span>
                    </td>
                    <td className={`px-3 py-2.5 whitespace-nowrap ${getLatencyColor(log.response_ms)}`}>
                      {log.response_ms !== null && log.response_ms !== undefined ? `${log.response_ms} ms` : '-'}
                    </td>
                    <td className="px-3 py-2.5 whitespace-nowrap text-slate-400">
                      {log.user_id || '-'}
                    </td>
                    <td className="px-4 py-2.5 max-w-md truncate text-slate-200 font-sans text-xs">
                      {log.message}
                    </td>
                    <td className="px-3 py-2.5 text-right whitespace-nowrap">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="p-1 hover:bg-slate-700 text-slate-400 hover:text-indigo-400 rounded transition"
                        title="View details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-950 border-t border-slate-800 text-xs text-slate-400">
          <div>
            Page <strong className="text-slate-200">{page}</strong> of{' '}
            <strong className="text-slate-200">{totalPages}</strong>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded bg-slate-900 border border-slate-800 disabled:opacity-40 hover:bg-slate-800 text-slate-300"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded bg-slate-900 border border-slate-800 disabled:opacity-40 hover:bg-slate-800 text-slate-300"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-0.5 rounded border text-xs font-mono font-bold ${getSeverityBadge(selectedLog.severity)}`}>
                  {selectedLog.severity}
                </span>
                <span className="text-sm font-mono text-slate-200 font-bold">
                  {selectedLog.event_id}
                </span>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">Service</span>
                <span className="text-slate-200">{selectedLog.service}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">Timestamp (UTC)</span>
                <span className="text-slate-200">{selectedLog.timestamp}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">Response Time</span>
                <span className={getLatencyColor(selectedLog.response_ms)}>
                  {selectedLog.response_ms !== null ? `${selectedLog.response_ms} ms` : 'N/A'}
                </span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">User ID</span>
                <span className="text-slate-200">{selectedLog.user_id || 'N/A'}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">Endpoint / Path</span>
                <span className="text-slate-200">{selectedLog.endpoint || 'N/A'}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">HTTP Status</span>
                <span className="text-slate-200">{selectedLog.http_status || 'N/A'}</span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-xs text-slate-500 font-mono">Message Payload:</span>
              <div className="bg-slate-950 border border-slate-800 rounded p-3 text-xs text-slate-200 font-sans">
                {selectedLog.message}
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-xs text-slate-500 font-mono">Raw Database Entity JSON:</span>
              <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-[11px] font-mono text-indigo-300 overflow-x-auto max-h-40">
                {JSON.stringify(selectedLog, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

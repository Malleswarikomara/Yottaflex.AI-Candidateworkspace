import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { ShieldAlert, CheckCircle2, ChevronLeft, ChevronRight, Eye, X, Filter } from 'lucide-react';
import { api } from '../services/api';
import MetricCard from '../components/MetricCard';

export default function DataQualityTab({ runs }) {
  const [rejectedLogs, setRejectedLogs] = useState([]);
  const [reasonStats, setReasonStats] = useState({ total_rejected: 0, reasons_breakdown: [] });
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [reasonFilter, setReasonFilter] = useState('');
  const [selectedReject, setSelectedReject] = useState(null);

  const fetchRejectedData = async () => {
    setLoading(true);
    try {
      const listData = await api.getRejectedLogs({
        page,
        limit,
        reason: reasonFilter || undefined,
      });
      setRejectedLogs(listData.items || []);
      setTotalRecords(listData.total_records || 0);
      setTotalPages(listData.total_pages || 1);

      const statsData = await api.getRejectedStats();
      setReasonStats(statsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRejectedData();
  }, [page, limit, reasonFilter]);

  const COLORS = ['#ef4444', '#f97316', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];

  const totalInputAllRuns = (runs || []).reduce((acc, r) => acc + (r.total_input_records || 0), 0);
  const totalValidAllRuns = (runs || []).reduce((acc, r) => acc + (r.valid_records || 0), 0);
  const totalRejectsAllRuns = (runs || []).reduce((acc, r) => acc + (r.rejected_records || 0), 0);
  const isAllReconciled = totalInputAllRuns === (totalValidAllRuns + totalRejectsAllRuns);

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-100">
          Data Quality & Quarantine Observability
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Zero silent discards: Isolated corrupt, duplicate, and malformed log entries with full source traceability.
        </p>
      </div>

      {/* Reconciliation Conservation Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-200">
                End-to-End Conservation & Audit Proof
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Total Ingested = Cleaned Target Records + Quarantined Records
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
              <span className="text-slate-500 block">Total Input</span>
              <span className="text-slate-200 font-bold">{totalInputAllRuns.toLocaleString()}</span>
            </div>
            <span className="text-slate-600 font-bold">=</span>
            <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
              <span className="text-slate-500 block">Valid DB Rows</span>
              <span className="text-emerald-400 font-bold">{totalValidAllRuns.toLocaleString()}</span>
            </div>
            <span className="text-slate-600 font-bold">+</span>
            <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
              <span className="text-slate-500 block">Quarantine Rows</span>
              <span className="text-rose-400 font-bold">{totalRejectsAllRuns.toLocaleString()}</span>
            </div>
            <div className="px-3 py-2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
              {isAllReconciled ? '✓ 100% RECONCILED' : 'DISCREPANCY DETECTED'}
            </div>
          </div>
        </div>
      </div>

      {/* Quarantined Reasons Frequency Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Rejection Reasons Distribution</h2>
            <p className="text-xs text-slate-500 font-mono">Frequency of Data Quality Failures</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Total Quarantined: <strong className="text-rose-400">{reasonStats.total_rejected.toLocaleString()}</strong>
          </span>
        </div>
        <div className="h-64">
          {reasonStats.reasons_breakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={reasonStats.reasons_breakdown}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 140, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis
                  dataKey="reason"
                  type="category"
                  stroke="#94a3b8"
                  fontSize={10}
                  tickLine={false}
                  width={140}
                  tickFormatter={(val) => (val.length > 25 ? `${val.substring(0, 23)}...` : val)}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  formatter={(val, name, item) => [`${val} records (${item.payload.percentage}%)`, 'Count']}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {reasonStats.reasons_breakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              No rejected records recorded
            </div>
          )}
        </div>
      </div>

      {/* Quarantined Records Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm space-y-3 p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-200">
            Quarantine Audit Log (`rejected_logs`)
          </h2>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="Filter by reason keyword..."
              value={reasonFilter}
              onChange={(e) => { setReasonFilter(e.target.value); setPage(1); }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-3 py-2.5">Reject ID</th>
                <th className="px-3 py-2.5">Run ID</th>
                <th className="px-3 py-2.5">Source File</th>
                <th className="px-3 py-2.5">Rejection Reason</th>
                <th className="px-4 py-2.5">Raw Record Preview</th>
                <th className="px-3 py-2.5 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-slate-500">
                    Loading quarantined records...
                  </td>
                </tr>
              ) : rejectedLogs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-slate-500">
                    No quarantined records found
                  </td>
                </tr>
              ) : (
                rejectedLogs.map((rej) => (
                  <tr key={rej.reject_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3 py-2 text-slate-400">#{rej.reject_id}</td>
                    <td className="px-3 py-2 text-indigo-400">{rej.run_id}</td>
                    <td className="px-3 py-2 text-slate-300">{rej.source_file}</td>
                    <td className="px-3 py-2">
                      <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 text-[11px] font-semibold">
                        {rej.reason}
                      </span>
                    </td>
                    <td className="px-4 py-2 max-w-sm truncate text-slate-400 text-[11px]">
                      {rej.raw_record}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => setSelectedReject(rej)}
                        className="p-1 hover:bg-slate-700 text-slate-400 hover:text-indigo-400 rounded transition"
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
        <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs text-slate-400">
          <div>
            Showing <strong className="text-slate-200">{rejectedLogs.length}</strong> of{' '}
            <strong className="text-slate-200">{totalRecords.toLocaleString()}</strong> quarantined items
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded bg-slate-900 border border-slate-800 disabled:opacity-40 hover:bg-slate-800 text-slate-300"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-slate-200">
              {page} / {totalPages}
            </span>
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

      {/* Rejection Detail Modal */}
      {selectedReject && (
        <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-3">
                <ShieldAlert className="w-5 h-5 text-rose-400" />
                <span className="text-sm font-mono text-slate-200 font-bold">
                  Quarantine Inspection #{selectedReject.reject_id}
                </span>
              </div>
              <button
                onClick={() => setSelectedReject(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">Run ID</span>
                <span className="text-indigo-400">{selectedReject.run_id}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-slate-500 block">Source File</span>
                <span className="text-slate-200">{selectedReject.source_file}</span>
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800 col-span-2">
                <span className="text-slate-500 block">Rejection Reason</span>
                <span className="text-rose-400 font-bold">{selectedReject.reason}</span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-xs text-slate-500 font-mono">Original Unparsed Raw Record:</span>
              <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-xs font-mono text-slate-200 whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                {selectedReject.raw_record}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

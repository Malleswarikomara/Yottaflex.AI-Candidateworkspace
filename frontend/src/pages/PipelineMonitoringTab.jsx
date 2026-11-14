import React, { useState } from 'react';
import { Database, CheckCircle2, AlertTriangle, XCircle, Clock, Eye, X } from 'lucide-react';
import { api } from '../services/api';

export default function PipelineMonitoringTab({ runs, onRefresh }) {
  const [selectedRun, setSelectedRun] = useState(null);
  const [runDetails, setRunDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const handleInspectRun = async (run) => {
    setSelectedRun(run);
    setLoadingDetails(true);
    try {
      const data = await api.getPipelineRunDetails(run.run_id);
      setRunDetails(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 text-[11px] font-semibold">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>SUCCESS</span>
          </span>
        );
      case 'PARTIAL_SUCCESS':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800 text-[11px] font-semibold">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>PARTIAL</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 text-[11px] font-semibold">
            <XCircle className="w-3 h-3 text-rose-400" />
            <span>FAILED</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
            <Clock className="w-3 h-3 text-slate-400" />
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100">
            Pipeline Execution & Observability Audit
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Historical trace of all batch ingestion runs, latency, throughput, and audit reconciliation logs.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono border border-slate-700 transition"
        >
          Refresh Runs
        </button>
      </div>

      {/* Runs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Run ID</th>
                <th className="px-3 py-3">Source File</th>
                <th className="px-3 py-3">Format</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Duration</th>
                <th className="px-3 py-3">Total Input</th>
                <th className="px-3 py-3">Valid DB</th>
                <th className="px-3 py-3">Quarantined</th>
                <th className="px-3 py-3">Reconciliation</th>
                <th className="px-3 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {runs && runs.length > 0 ? (
                runs.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-2.5 font-bold text-indigo-400">{run.run_id}</td>
                    <td className="px-3 py-2.5 text-slate-200">{run.source_file}</td>
                    <td className="px-3 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {run.file_format}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">{getStatusBadge(run.status)}</td>
                    <td className="px-3 py-2.5 text-slate-400">{run.duration_seconds}s</td>
                    <td className="px-3 py-2.5 font-bold text-slate-200">{run.total_input_records.toLocaleString()}</td>
                    <td className="px-3 py-2.5 text-emerald-400 font-bold">{run.valid_records.toLocaleString()}</td>
                    <td className="px-3 py-2.5 text-rose-400 font-bold">{run.rejected_records.toLocaleString()}</td>
                    <td className="px-3 py-2.5">
                      {run.is_reconciled ? (
                        <span className="text-emerald-400 flex items-center space-x-1">
                          <span>✓ Verified</span>
                        </span>
                      ) : (
                        <span className="text-rose-400 font-bold">✗ Mismatch</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <button
                        onClick={() => handleInspectRun(run)}
                        className="p-1 hover:bg-slate-700 text-slate-400 hover:text-indigo-400 rounded transition"
                        title="Inspect run audit"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="10" className="text-center py-10 text-slate-500">
                    No pipeline runs recorded yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Run Inspection Modal */}
      {selectedRun && (
        <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5 text-indigo-400" />
                <span className="text-sm font-mono text-slate-200 font-bold">
                  Pipeline Run Audit: {selectedRun.run_id}
                </span>
              </div>
              <button
                onClick={() => { setSelectedRun(null); setRunDetails(null); }}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingDetails ? (
              <div className="py-12 text-center text-xs text-slate-500 font-mono">
                Loading run details...
              </div>
            ) : runDetails ? (
              <div className="space-y-4">
                {/* Reconciliation Audit Formula */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase font-mono tracking-wider">
                    Source-to-Target Conservation Law:
                  </span>
                  <div className="flex items-center space-x-4 text-xs font-mono pt-1">
                    <div>
                      <span className="text-slate-500 block">Total Input</span>
                      <span className="text-slate-200 font-bold text-sm">
                        {runDetails.reconciliation.total_input_records.toLocaleString()}
                      </span>
                    </div>
                    <span className="text-slate-600 font-bold text-lg">=</span>
                    <div>
                      <span className="text-slate-500 block">Cleaned Target</span>
                      <span className="text-emerald-400 font-bold text-sm">
                        {runDetails.reconciliation.valid_records.toLocaleString()}
                      </span>
                    </div>
                    <span className="text-slate-600 font-bold text-lg">+</span>
                    <div>
                      <span className="text-slate-500 block">Quarantined</span>
                      <span className="text-rose-400 font-bold text-sm">
                        {runDetails.reconciliation.rejected_records.toLocaleString()}
                      </span>
                    </div>
                    <div className="ml-auto px-3 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-bold">
                      {runDetails.reconciliation.is_reconciled ? '✓ 100% RECONCILED' : 'RECONCILIATION FAILURE'}
                    </div>
                  </div>
                </div>

                {/* Aggregated Service Metrics */}
                {runDetails.metrics && runDetails.metrics.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase font-mono tracking-wider">
                      Recorded Service Metrics (`log_metrics`):
                    </span>
                    <div className="overflow-x-auto border border-slate-800 rounded-lg">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-950 text-slate-400 text-[10px]">
                          <tr>
                            <th className="px-3 py-2">Service</th>
                            <th className="px-3 py-2">Logs</th>
                            <th className="px-3 py-2">Errors</th>
                            <th className="px-3 py-2">Error %</th>
                            <th className="px-3 py-2">Avg Latency</th>
                            <th className="px-3 py-2">P95 Latency</th>
                            <th className="px-3 py-2">Max Latency</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {runDetails.metrics.map((m) => (
                            <tr key={m.metric_id}>
                              <td className="px-3 py-2 text-slate-300 font-bold">{m.service}</td>
                              <td className="px-3 py-2 text-slate-400">{m.total_logs}</td>
                              <td className="px-3 py-2 text-rose-400">{m.error_count + m.critical_count}</td>
                              <td className="px-3 py-2 text-amber-400">{m.error_rate_pct}%</td>
                              <td className="px-3 py-2 text-slate-300">{m.avg_latency_ms} ms</td>
                              <td className="px-3 py-2 text-indigo-400">{m.p95_latency_ms} ms</td>
                              <td className="px-3 py-2 text-rose-400">{m.max_latency_ms} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

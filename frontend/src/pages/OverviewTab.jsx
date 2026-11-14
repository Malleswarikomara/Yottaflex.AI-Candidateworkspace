import React from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { Database, AlertTriangle, Clock, Activity, CheckCircle2, Server, Globe, RotateCcw } from 'lucide-react';
import MetricCard from '../components/MetricCard';

export default function OverviewTab({ stats, runs, onRefresh }) {
  const sevData = [
    { name: 'INFO', value: stats?.severity_counts?.INFO || 0, color: '#3b82f6' },
    { name: 'WARNING', value: stats?.severity_counts?.WARNING || 0, color: '#f59e0b' },
    { name: 'ERROR', value: stats?.severity_counts?.ERROR || 0, color: '#ef4444' },
    { name: 'CRITICAL', value: stats?.severity_counts?.CRITICAL || 0, color: '#dc2626' },
  ].filter(d => d.value > 0);

  const serviceData = (stats?.services_breakdown || []).map(s => ({
    service: s.service,
    total: s.total_logs,
    errors: s.error_count + s.critical_count,
    rate: s.error_rate_pct,
    avg_latency: s.avg_latency_ms || 0,
  }));

  const latestRun = runs && runs.length > 0 ? runs[0] : null;

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100">
            Platform Observability & Metrics Overview
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time pipeline ingestion health, normalized log volumes, decoupled error rates, and API latency analytics.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition flex items-center space-x-2"
        >
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* KPI Cards Row - 5 Decoupled Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Ingested Logs"
          value={stats?.total_logs ? stats.total_logs.toLocaleString() : '0'}
          subtitle="Cleaned & validated in DB"
          icon={Database}
          color="indigo"
        />
        <MetricCard
          title="Severity Error Rate"
          value={`${stats?.error_rate_pct !== undefined ? stats.error_rate_pct : 0}%`}
          subtitle="Formula: (Error + Crit) / Total"
          icon={AlertTriangle}
          color={stats?.error_rate_pct > 15 ? 'rose' : stats?.error_rate_pct > 5 ? 'amber' : 'emerald'}
          badge={{
            text: stats?.error_rate_pct > 10 ? 'High' : 'Normal',
            type: stats?.error_rate_pct > 10 ? 'red' : 'green',
          }}
        />
        <MetricCard
          title="HTTP Failure Rate"
          value={`${stats?.http_failure_rate_pct !== undefined ? stats.http_failure_rate_pct : 0}%`}
          subtitle={`${stats?.http_failure_count || 0} failures / ${stats?.http_request_count || 0} reqs (>=500)`}
          icon={Globe}
          color={stats?.http_failure_rate_pct > 10 ? 'rose' : stats?.http_failure_rate_pct > 3 ? 'amber' : 'emerald'}
          badge={{
            text: 'HTTP 5xx',
            type: stats?.http_failure_rate_pct > 5 ? 'red' : 'green',
          }}
        />
        <MetricCard
          title="Avg API Latency"
          value={`${stats?.latency?.avg_ms || 0} ms`}
          subtitle={`Min: ${stats?.latency?.min_ms || 0}ms | Max: ${stats?.latency?.max_ms || 0}ms`}
          icon={Clock}
          color="sky"
        />
        <MetricCard
          title="P95 Tail Latency"
          value={`${stats?.latency?.p95_ms || 0} ms`}
          subtitle={`Median (P50): ${stats?.latency?.p50_ms || 0} ms`}
          icon={Activity}
          color="amber"
          badge={{
            text: '95th Percentile',
            type: 'amber',
          }}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution Donut */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200">Severity Distribution</h2>
            <span className="text-xs text-slate-500 font-mono">Normalized Log Levels</span>
          </div>
          <div className="h-64">
            {sevData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sevData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {sevData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No log data available yet
              </div>
            )}
          </div>
        </div>

        {/* Per-Service Logs & Errors Bar Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200">Service Workload & Error Breakdown</h2>
            <span className="text-xs text-slate-500 font-mono">Target Entities</span>
          </div>
          <div className="h-64">
            {serviceData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={serviceData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="service" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
                  <Bar dataKey="total" name="Total Logs" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="errors" name="Errors + Critical" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No service data available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Latest Execution & Reconciliation Banner */}
      {latestRun && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-slate-200">
                    Latest Pipeline Run: {latestRun.run_id}
                  </span>
                  <span className={`px-2 py-0.5 text-xs font-mono rounded ${
                    latestRun.status === 'SUCCESS'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      : latestRun.status === 'PARTIAL_SUCCESS'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-rose-950 text-rose-300 border border-rose-800'
                  }`}>
                    {latestRun.status}
                  </span>
                  {latestRun.retry_count > 0 && (
                    <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-800 text-amber-300 border border-slate-700 flex items-center space-x-1">
                      <RotateCcw className="w-2.5 h-2.5" />
                      <span>Retries: {latestRun.retry_count}</span>
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Source: <span className="font-mono text-slate-300">{latestRun.source_file}</span> ({latestRun.file_format}) • Processed in <span className="text-indigo-400 font-mono">{latestRun.duration_seconds}s</span>
                </p>
              </div>
            </div>

            {/* Reconciliation Proof Tag: Input = Inserted + Rejected + Skipped */}
            <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
              <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Total Input</span>
                <span className="text-slate-200 font-bold">{latestRun.total_input_records.toLocaleString()}</span>
              </div>
              <div className="text-slate-600 font-bold">=</div>
              <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Newly Inserted</span>
                <span className="text-emerald-400 font-bold">
                  {(latestRun.newly_inserted_records !== undefined && latestRun.newly_inserted_records !== null ? latestRun.newly_inserted_records : latestRun.valid_records).toLocaleString()}
                </span>
              </div>
              <div className="text-slate-600 font-bold">+</div>
              <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Quarantined</span>
                <span className="text-rose-400 font-bold">{latestRun.rejected_records.toLocaleString()}</span>
              </div>
              <div className="text-slate-600 font-bold">+</div>
              <div className="bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Previously Skipped</span>
                <span className="text-sky-400 font-bold">{(latestRun.previously_skipped_records || 0).toLocaleString()}</span>
              </div>
              <div className={`px-3 py-2 rounded font-bold ${
                latestRun.is_reconciled
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-rose-950 text-rose-300 border border-rose-800'
              }`}>
                {latestRun.is_reconciled ? '✓ 100% RECONCILED' : 'RECONCILIATION MISMATCH'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

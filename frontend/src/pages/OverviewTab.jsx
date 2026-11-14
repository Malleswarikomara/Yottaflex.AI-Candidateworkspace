import React from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { Database, AlertTriangle, Clock, Activity, CheckCircle2, Server } from 'lucide-react';
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
            Real-time pipeline ingestion health, normalized log volumes, and API latency analytics.
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

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Ingested Logs"
          value={stats?.total_logs ? stats.total_logs.toLocaleString() : '0'}
          subtitle="Cleaned & validated in DB"
          icon={Database}
          color="indigo"
        />
        <MetricCard
          title="Global Error Rate"
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
          icon={Gauge}
          color="amber"
          badge={{
            text: '95th Percentile',
            type: 'amber',
          }}
        />
        <MetricCard
          title="Failed Requests"
          value={stats?.failed_requests ? stats.failed_requests.toLocaleString() : '0'}
          subtitle="HTTP >= 500 or Error/Crit"
          icon={Server}
          color="rose"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution Donut */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200">Severity Distribution</h2>
            <span className="text-xs text-slate-500 font-mono">ISO Normalization</span>
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
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-slate-200">
                    Latest Pipeline Run: {latestRun.run_id}
                  </span>
                  <span className="px-2 py-0.5 text-xs font-mono rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                    {latestRun.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Source: <span className="font-mono text-slate-300">{latestRun.source_file}</span> ({latestRun.file_format}) • Processed in <span className="text-indigo-400 font-mono">{latestRun.duration_seconds}s</span>
                </p>
              </div>
            </div>

            {/* Reconciliation Proof Tag */}
            <div className="flex items-center space-x-6 text-xs font-mono">
              <div>
                <span className="text-slate-500 block">Total Input</span>
                <span className="text-slate-200 font-bold">{latestRun.total_input_records.toLocaleString()}</span>
              </div>
              <div className="text-slate-600">=</div>
              <div>
                <span className="text-slate-500 block">Valid Target</span>
                <span className="text-emerald-400 font-bold">{latestRun.valid_records.toLocaleString()}</span>
              </div>
              <div className="text-slate-600">+</div>
              <div>
                <span className="text-slate-500 block">Quarantined</span>
                <span className="text-rose-400 font-bold">{latestRun.rejected_records.toLocaleString()}</span>
              </div>
              <div className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {latestRun.is_reconciled ? '✓ 100% RECONCILED' : 'RECONCILIATION MISMATCH'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Gauge(props) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 14 4-4" />
      <path d="M3.34 19a10 10 0 1 1 17.32 0" />
    </svg>
  );
}

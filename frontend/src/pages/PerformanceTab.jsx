import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend
} from 'recharts';
import { Gauge, Zap, AlertCircle, Clock, Server } from 'lucide-react';
import { api } from '../services/api';
import MetricCard from '../components/MetricCard';

export default function PerformanceTab({ stats }) {
  const [distribution, setDistribution] = useState([]);
  const [slowLogs, setSlowLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const distData = await api.getLatencyDistribution();
        setDistribution(distData.buckets || []);

        const slow = await api.getLogs({
          min_response_ms: 1000,
          limit: 10,
        });
        setSlowLogs(slow.items || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const serviceLatencyData = (stats?.services_breakdown || []).map((s) => ({
    service: s.service,
    avg: s.avg_latency_ms || 0,
    max: s.max_latency_ms || 0,
  }));

  const getBucketColor = (range) => {
    switch (range) {
      case '0-100ms': return '#10b981';
      case '100-300ms': return '#3b82f6';
      case '300-500ms': return '#6366f1';
      case '500-1000ms': return '#f59e0b';
      case '1000-3000ms': return '#f97316';
      case '>3000ms': return '#ef4444';
      default: return '#64748b';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-100">
          API Latency & Performance Diagnostics
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Detailed response time percentiles, SLA thresholds, and tail latency distributions.
        </p>
      </div>

      {/* Latency Percentiles Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Average Latency"
          value={`${stats?.latency?.avg_ms || 0} ms`}
          subtitle="Mean response time"
          icon={Clock}
          color="indigo"
        />
        <MetricCard
          title="Median Latency (P50)"
          value={`${stats?.latency?.p50_ms || 0} ms`}
          subtitle="50% of requests faster"
          icon={Zap}
          color="sky"
        />
        <MetricCard
          title="95th Percentile (P95)"
          value={`${stats?.latency?.p95_ms || 0} ms`}
          subtitle="5% requests degraded"
          icon={Gauge}
          color="amber"
          badge={{ text: 'P95 SLA', type: 'amber' }}
        />
        <MetricCard
          title="99th Percentile (P99)"
          value={`${stats?.latency?.p99_ms || 0} ms`}
          subtitle="Extreme tail latency"
          icon={AlertCircle}
          color="rose"
        />
        <MetricCard
          title="Maximum Recorded"
          value={`${stats?.latency?.max_ms || 0} ms`}
          subtitle="Worst-case latency peak"
          icon={Server}
          color="rose"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latency Distribution Histogram */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Response Time Distribution</h2>
              <p className="text-xs text-slate-500 font-mono">Sample Count by Latency Bracket</p>
            </div>
            <span className="text-xs text-indigo-400 font-mono">NIST Percentiles</span>
          </div>
          <div className="h-64">
            {distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distribution} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="range" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                    formatter={(val, name, item) => [`${val} logs (${item.payload.percentage}%)`, 'Volume']}
                  />
                  <Bar dataKey="count" name="Logs" radius={[4, 4, 0, 0]}>
                    {distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getBucketColor(entry.range)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                Loading latency samples...
              </div>
            )}
          </div>
        </div>

        {/* Avg vs Max Response Time by Service */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Service Response Times</h2>
              <p className="text-xs text-slate-500 font-mono">Average vs Maximum Latency (ms)</p>
            </div>
            <span className="text-xs text-slate-400 font-mono">SLA Breakdown</span>
          </div>
          <div className="h-64">
            {serviceLatencyData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={serviceLatencyData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="service" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
                  <Bar dataKey="avg" name="Avg Latency (ms)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="max" name="Max Latency (ms)" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No latency statistics available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Slow Request Outliers Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">
              Slow Request Outliers (&gt; 1,000 ms SLA Threshold)
            </h2>
            <p className="text-xs text-slate-500 font-mono">
              Requests exceeding standard latency budgets for proactive optimization
            </p>
          </div>
          <span className="text-xs text-rose-400 font-mono font-bold">High Priority</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-3 py-2.5">Event ID</th>
                <th className="px-3 py-2.5">Service</th>
                <th className="px-3 py-2.5">Severity</th>
                <th className="px-3 py-2.5">Latency</th>
                <th className="px-3 py-2.5">User</th>
                <th className="px-4 py-2.5">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {slowLogs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-6 text-slate-500">
                    No requests exceeded the 1,000ms threshold
                  </td>
                </tr>
              ) : (
                slowLogs.map((log) => (
                  <tr key={log.event_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3 py-2 text-indigo-400 font-bold">{log.event_id}</td>
                    <td className="px-3 py-2 text-slate-300">{log.service}</td>
                    <td className="px-3 py-2">
                      <span className="text-rose-400 font-semibold">{log.severity}</span>
                    </td>
                    <td className="px-3 py-2 text-rose-400 font-bold">{log.response_ms} ms</td>
                    <td className="px-3 py-2 text-slate-400">{log.user_id || '-'}</td>
                    <td className="px-4 py-2 text-slate-200 font-sans max-w-sm truncate">{log.message}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = {
  // System Health
  async getHealth() {
    const res = await fetch(`${BASE_URL}/api/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  // Overview Stats
  async getStats(runId = '', service = '') {
    const params = new URLSearchParams();
    if (runId) params.append('run_id', runId);
    if (service) params.append('service', service);
    const res = await fetch(`${BASE_URL}/api/logs/stats?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },

  // Logs Explorer
  async getLogs(params = {}) {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        q.append(k, v);
      }
    });
    const res = await fetch(`${BASE_URL}/api/logs?${q.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch logs');
    return res.json();
  },

  // Latency Distribution
  async getLatencyDistribution(runId = '') {
    const params = new URLSearchParams();
    if (runId) params.append('run_id', runId);
    const res = await fetch(`${BASE_URL}/api/logs/latency-distribution?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch latency distribution');
    return res.json();
  },

  // Quarantined Rejections
  async getRejectedLogs(params = {}) {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        q.append(k, v);
      }
    });
    const res = await fetch(`${BASE_URL}/api/rejected?${q.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch rejected logs');
    return res.json();
  },

  // Rejection Stats
  async getRejectedStats(runId = '') {
    const params = new URLSearchParams();
    if (runId) params.append('run_id', runId);
    const res = await fetch(`${BASE_URL}/api/rejected/stats?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch rejection stats');
    return res.json();
  },

  // Pipeline Execution Runs
  async getPipelineRuns(limit = 50) {
    const res = await fetch(`${BASE_URL}/api/pipeline/runs?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch pipeline runs');
    return res.json();
  },

  async getPipelineRunDetails(runId) {
    const res = await fetch(`${BASE_URL}/api/pipeline/runs/${runId}`);
    if (!res.ok) throw new Error('Failed to fetch run details');
    return res.json();
  },

  // File Upload Ingestion
  async uploadFile(file, runId = '') {
    const formData = new FormData();
    formData.append('file', file);
    if (runId) formData.append('run_id', runId);

    const res = await fetch(`${BASE_URL}/api/pipeline/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  // Execute Sample Dataset
  async runSample(sampleName = 'sample_logs.csv') {
    const res = await fetch(`${BASE_URL}/api/pipeline/run-sample?sample_name=${sampleName}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to run sample dataset');
    return res.json();
  },

  // Synthetic Data Generator
  async generateSynthetic(count = 1000, format = 'json', anomalyRatio = 0.03, autoIngest = true) {
    const res = await fetch(`${BASE_URL}/api/pipeline/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count, format, anomaly_ratio: anomalyRatio, auto_ingest: autoIngest }),
    });
    if (!res.ok) throw new Error('Failed to generate synthetic dataset');
    return res.json();
  },

  // Aggregated Metrics
  async getMetrics(runId = '', service = '') {
    const params = new URLSearchParams();
    if (runId) params.append('run_id', runId);
    if (service) params.append('service', service);
    const res = await fetch(`${BASE_URL}/api/metrics?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  },
};

import React, { useState } from 'react';
import { UploadCloud, Play, Sparkles, CheckCircle2, AlertCircle, FileText, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

export default function IngestionCenterTab({ onPipelineSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [runningSample, setRunningSample] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Synthetic Generator State
  const [genCount, setGenCount] = useState(1000);
  const [genFormat, setGenFormat] = useState('csv');
  const [anomalyRatio, setAnomalyRatio] = useState(0.03);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.uploadFile(file);
      setResult(data);
      if (onPipelineSuccess) onPipelineSuccess();
    } catch (err) {
      setError(err.message || 'File upload and ingestion failed');
    } finally {
      setUploading(false);
    }
  };

  const handleRunSample = async (sampleName) => {
    setRunningSample(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.runSample(sampleName);
      setResult(data);
      if (onPipelineSuccess) onPipelineSuccess();
    } catch (err) {
      setError(err.message || 'Failed to process sample file');
    } finally {
      setRunningSample(false);
    }
  };

  const handleGenerateSynthetic = async () => {
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.generateSynthetic(Number(genCount), genFormat, Number(anomalyRatio), true);
      setResult(data.pipeline_result);
      if (onPipelineSuccess) onPipelineSuccess();
    } catch (err) {
      setError(err.message || 'Synthetic data generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Banner */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-100">
          Data Ingestion & Dataset Generator Hub
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Ingest structured or semi-structured application logs from local files, run reproducible benchmarks, or trigger high-volume synthetic generators.
        </p>
      </div>

      {/* Grid of Ingestion Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Custom File Upload Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Upload Application Log File</h2>
              <p className="text-xs text-slate-500">Supports .csv, .json, .jsonl, .log, and .txt</p>
            </div>
          </div>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="border-2 border-dashed border-slate-800 hover:border-slate-700 rounded-xl p-6 text-center cursor-pointer transition bg-slate-950/40">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileChange}
                accept=".csv,.json,.jsonl,.ndjson,.log,.txt"
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer space-y-2 block">
                <FileText className="w-8 h-8 text-slate-500 mx-auto" />
                <span className="text-xs text-slate-300 block font-medium">
                  {file ? file.name : 'Click to browse or drag and drop log file'}
                </span>
                <span className="text-[11px] text-slate-500 block">
                  {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Automatic format detection & schema sniffing'}
                </span>
              </label>
            </div>

            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-xs font-semibold font-mono transition flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/20"
            >
              {uploading ? (
                <span>Ingesting & Reconciling...</span>
              ) : (
                <>
                  <span>Ingest Selected File</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* 2. Scalable Synthetic Generator Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Scalable Synthetic Generator</h2>
              <p className="text-xs text-slate-500">Benchmark up to 100,000+ records with fixed random seed</p>
            </div>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div>
              <label className="text-slate-400 block mb-1">Record Count:</label>
              <select
                value={genCount}
                onChange={(e) => setGenCount(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
              >
                <option value="1000">1,000 records (Starter Sample)</option>
                <option value="5000">5,000 records</option>
                <option value="10000">10,000 records</option>
                <option value="50000">50,000 records</option>
                <option value="100000">100,000 records (Full Benchmark)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Payload Format:</label>
                <select
                  value={genFormat}
                  onChange={(e) => setGenFormat(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                >
                  <option value="csv">CSV Format</option>
                  <option value="json">JSON Array</option>
                  <option value="text">Semi-structured TEXT (.log)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Anomaly Ratio:</label>
                <select
                  value={anomalyRatio}
                  onChange={(e) => setAnomalyRatio(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                >
                  <option value="0.01">1% Anomalies</option>
                  <option value="0.03">3% (Recommended)</option>
                  <option value="0.05">5% Anomalies</option>
                  <option value="0.10">10% Heavy Chaos</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleGenerateSynthetic}
              disabled={generating}
              className="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded-lg text-xs font-semibold font-mono transition flex items-center justify-center space-x-2 shadow-lg shadow-sky-600/20"
            >
              {generating ? (
                <span>Generating & Ingesting Dataset...</span>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Generate & Ingest {genCount.toLocaleString()} Records</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 3. Reproducible Sample Dataset Presets */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
        <h2 className="text-sm font-semibold text-slate-200">
          Quick-Start Reproducible Dataset Presets
        </h2>
        <p className="text-xs text-slate-400">
          Pre-generated sample files available in <code className="text-indigo-400 font-mono">data/sample/</code> for instant review.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <button
            onClick={() => handleRunSample('sample_logs.csv')}
            disabled={runningSample}
            className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500/50 rounded-lg text-left transition group"
          >
            <span className="text-xs font-mono font-bold text-slate-200 block group-hover:text-indigo-400">
              sample_logs.csv
            </span>
            <span className="text-[11px] text-slate-500 block">1,000 CSV Rows</span>
          </button>

          <button
            onClick={() => handleRunSample('sample_logs.json')}
            disabled={runningSample}
            className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500/50 rounded-lg text-left transition group"
          >
            <span className="text-xs font-mono font-bold text-slate-200 block group-hover:text-indigo-400">
              sample_logs.json
            </span>
            <span className="text-[11px] text-slate-500 block">1,000 JSON Array</span>
          </button>

          <button
            onClick={() => handleRunSample('sample_logs.log')}
            disabled={runningSample}
            className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500/50 rounded-lg text-left transition group"
          >
            <span className="text-xs font-mono font-bold text-slate-200 block group-hover:text-indigo-400">
              sample_logs.log
            </span>
            <span className="text-[11px] text-slate-500 block">1,000 Text Lines</span>
          </button>

          <button
            onClick={() => handleRunSample('quick_starter.json')}
            disabled={runningSample}
            className="p-3 bg-slate-950 border border-slate-800 hover:border-indigo-500/50 rounded-lg text-left transition group"
          >
            <span className="text-xs font-mono font-bold text-slate-200 block group-hover:text-indigo-400">
              quick_starter.json
            </span>
            <span className="text-[11px] text-slate-500 block">100 Starter Logs</span>
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-rose-950/50 border border-rose-800 p-4 rounded-xl flex items-center space-x-3 text-xs text-rose-300 font-mono">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Live Ingestion Result Card */}
      {result && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4 animate-in fade-in duration-300">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-sm font-mono font-bold text-slate-200">
                  Execution Report: {result.run_id}
                </h3>
                <span className="text-xs text-slate-400">
                  File: <strong className="text-slate-200">{result.source_file}</strong> ({result.file_format})
                </span>
              </div>
            </div>
            <div className="text-right font-mono text-xs">
              <span className="px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                {result.status}
              </span>
              <span className="text-slate-500 block mt-1">{result.duration_seconds}s execution time</span>
            </div>
          </div>

          {/* Reconciliation Proof Banner */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase font-mono tracking-wider">
              Source-to-Target Conservation Law:
            </span>
            <div className="flex items-center space-x-6 text-xs font-mono pt-1">
              <div>
                <span className="text-slate-500 block">Input Records</span>
                <span className="text-slate-200 font-bold text-base">
                  {result.reconciliation.total_input_records.toLocaleString()}
                </span>
              </div>
              <span className="text-slate-600 font-bold text-lg">=</span>
              <div>
                <span className="text-slate-500 block">Target Inserted</span>
                <span className="text-emerald-400 font-bold text-base">
                  {result.reconciliation.valid_records.toLocaleString()}
                </span>
              </div>
              <span className="text-slate-600 font-bold text-lg">+</span>
              <div>
                <span className="text-slate-500 block">Quarantined</span>
                <span className="text-rose-400 font-bold text-base">
                  {result.reconciliation.rejected_records.toLocaleString()}
                </span>
              </div>
              <div className="ml-auto px-3 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-bold">
                {result.reconciliation.is_reconciled ? '✓ 100% RECONCILED' : 'RECONCILIATION FAILURE'}
              </div>
            </div>
          </div>

          {/* Operational Metrics Rollup */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <span className="text-slate-500 block">Batch Error Rate</span>
              <span className="text-amber-400 font-bold text-sm">
                {result.metrics_summary.error_rate_pct}%
              </span>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <span className="text-slate-500 block">Average Latency</span>
              <span className="text-sky-400 font-bold text-sm">
                {result.metrics_summary.avg_latency_ms || 0} ms
              </span>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <span className="text-slate-500 block">Intra-Batch Dupes</span>
              <span className="text-rose-400 font-bold text-sm">
                {result.reconciliation.intra_batch_duplicates}
              </span>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <span className="text-slate-500 block">DB Dupes Skipped</span>
              <span className="text-slate-300 font-bold text-sm">
                {result.reconciliation.db_duplicates_skipped}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

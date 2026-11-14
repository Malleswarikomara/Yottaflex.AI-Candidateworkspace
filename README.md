# Application Log Analytics & Monitoring Platform

A production-grade, three-tier Data Engineering platform designed to ingest, parse, validate, and normalize structured (CSV, JSON) and semi-structured (syslog/regex text) application logs, quarantine corrupt entries, prevent duplicates, and calculate real-time error rate and tail latency metrics.

---

## 1. Executive Summary & Problem Context

Modern distributed applications generate millions of log events across multiple microservices. These logs arrive in heterogeneous, noisy formats—some as structured CSV/JSON payloads, others as unstructured text lines with timestamps, error levels, and key-value attributes.

> [!NOTE]
> **Scope & Processing Mode:** The pipeline currently performs in-memory batch parsing and validation, chunked existing-ID lookups, and bulk database insertion. This approach is suitable for the demonstrated 100,000-record workload. Continuous streaming and bounded-memory chunked ingestion are outside the current implementation scope.

### Core Objectives
1. **Automated Multi-Format Ingestion:** Ingest CSV, JSON (Array & Lines), and semi-structured text logs with automatic format sniffing.
2. **Standardization & Normalization:**
   - Normalize varied timestamps into timezone-aware UTC ISO-8601 strings.
   - Canonicalize log severities to standard uppercase (`INFO`, `WARNING`, `ERROR`, `CRITICAL`).
   - Generate deterministic, collision-resistant event IDs (SHA-256) when missing.
3. **Data Quality & Zero Silent Loss:**
   - Strict schema validation detecting missing fields, unparseable timestamps, and negative response times.
   - Corrupt or duplicate records are quarantined in `rejected_logs` with the exact raw line, descriptive failure reason, and structured `reject_type` (`MALFORMED`, `VALIDATION_ERROR`, `DUPLICATE`, `SCHEMA_ERROR`).
4. **Idempotent Ingestion & Rerun Accounting:**
   - Primary key constraints on `event_id` and batch deduplication ensure identical reruns never create duplicate target rows.
   - Previously processed records are accounted for as `previously_skipped_records`.
5. **Decoupled Operational Analytics:**
   - Compute independent severity-based error rates and HTTP failure rates.
   - Calculate response time distributions: Average, Min, Max, Median (P50), P95, and P99 latency percentiles using NIST linear interpolation.

---

## 2. Three-Tier Decoupled Architecture

The platform strictly isolates presentation, business processing, and persistence layers:

```mermaid
flowchart TD
    subgraph Tier1["Tier 1: Presentation Layer (React.js + Vite + Tailwind CSS + Recharts)"]
        Overview["Overview Dashboard\n(KPI Cards, Severity Donut, Service Error Bars)"]
        Explorer["Log Explorer\n(Live Search, Multi-Filter, Pagination, JSON Modal)"]
        Perf["Performance Analytics\n(Latency Histogram, P95 SLAs, Tail Latency)"]
        Quality["Data Quality & Quarantine\n(Reconciliation Proof, Rejection Taxonomy & Reasons)"]
        Monitoring["Pipeline Monitoring\n(Execution Trace, Retries, Failure Reason, Audit Metrics)"]
        IngestionHub["Ingestion Hub\n(File Upload Dropzone, Synthetic Generator, Sample Presets)"]
    end

    subgraph Tier2["Tier 2: Business Logic & Orchestrator (Python 3.12 + FastAPI)"]
        FastAPI["FastAPI REST Endpoints (/api/pipeline, /api/logs, /api/rejected, /api/metrics)"]
        Sniffer["Format Sniffer & Parser Factory"]
        Parsers["CSV / JSON / Text Semi-Structured Parsers"]
        Validator["Schema Validation, Normalization & Intra-batch Deduplication"]
        MetricsEngine["Statistical Metrics Engine (Severity Error % vs HTTP Fail %)"]
    end

    subgraph Tier3["Tier 3: Persistence Layer (PostgreSQL / SQLite)"]
        RunsTable[("pipeline_runs\n(Batch Execution History, Retries & Audit Status)")]
        TargetTable[("application_logs\n(Valid Cleaned Canonical Logs)")]
        QuarantineTable[("rejected_logs\n(Quarantined Raw Records & reject_type)")]
        MetricsTable[("log_metrics\n(Pre-aggregated Service Performance Rollups)")]
    end

    IngestionHub -->|Multipart Upload / Synthetic Trigger| FastAPI
    FastAPI --> Sniffer
    Sniffer --> Parsers
    Parsers -->|Raw Extracted Records| Validator
    Validator -->|Valid Unique Records| TargetTable
    Validator -->|Corrupt / Missing / Duplicates| QuarantineTable
    Validator -->|Cleaned Ingest Stream| MetricsEngine
    MetricsEngine --> MetricsTable
    FastAPI --> RunsTable
    TargetTable -->|REST Queries| Explorer
    TargetTable -->|KPI Aggregates| Overview
    TargetTable -->|Latency Distribution| Perf
    QuarantineTable -->|Audit Inspection| Quality
    RunsTable -->|Execution History| Monitoring
```

---

## 3. Data Dictionary & Entity Relationships

The relational model supports high-throughput batch ingestion, query filtering, and auditability. The complete PostgreSQL DDL is located in [`database/schema.sql`](database/schema.sql).

### Table 1: `pipeline_runs`
- **Grain:** One record per batch ingestion execution (upload or synthetic run).
- **Primary Key:** `run_id` (VARCHAR 64, e.g. `RUN_20261114_091211_E07F62`).
- **Columns:**
  | Column Name | Data Type | Nullable | Description |
  | :--- | :--- | :--- | :--- |
  | `run_id` | VARCHAR(64) | NO | Deterministic / timestamped unique run identifier |
  | `source_file` | VARCHAR(255) | NO | Name of uploaded or generated source file |
  | `file_format` | VARCHAR(32) | NO | Detected syntax: `CSV`, `JSON`, `TEXT` |
  | `status` | VARCHAR(32) | NO | `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED` |
  | `start_time` | TIMESTAMP WITH TZ | NO | Pipeline start timestamp in UTC |
  | `end_time` | TIMESTAMP WITH TZ | YES | Pipeline completion timestamp in UTC |
  | `duration_seconds` | FLOAT | YES | Total wall-clock processing time in seconds |
  | `total_input_records` | INTEGER | NO | Total raw rows/objects parsed from input |
  | `valid_records` | INTEGER | NO | Total valid cleaned rows (backwards compatibility) |
  | `newly_inserted_records` | INTEGER | NO | Rows newly stored into `application_logs` in this run |
  | `rejected_records` | INTEGER | NO | Total rows quarantined in `rejected_logs` |
  | `previously_skipped_records` | INTEGER | NO | Previously stored records skipped during reruns |
  | `duplicate_records` | INTEGER | NO | Count of intra-batch duplicates and cross-batch skips |
  | `retry_count` | INTEGER | NO | Number of retry attempts executed |
  | `failure_reason` | TEXT | YES | Diagnostic message if processing failed |
  | `error_message` | TEXT | YES | Diagnostic stack trace if run failed |

### Table 2: `application_logs`
- **Grain:** One record per unique, validated application event.
- **Primary Key:** `event_id` (VARCHAR 64).
- **Columns & Constraints:**
  | Column Name | Data Type | Nullable | Description |
  | :--- | :--- | :--- | :--- |
  | `event_id` | VARCHAR(64) | NO | Unique event identifier (provided or deterministic SHA-256) |
  | `run_id` | VARCHAR(64) | NO | Foreign Key referencing `pipeline_runs.run_id` |
  | `timestamp` | TIMESTAMP WITH TZ | NO | Normalized UTC event timestamp (Indexed) |
  | `severity` | VARCHAR(20) | NO | Canonical level: `INFO`, `WARNING`, `ERROR`, `CRITICAL` (CHECK constraint) |
  | `service` | VARCHAR(64) | NO | Microservice name (e.g. `auth`, `payment`, `api-gateway`) (Indexed) |
  | `message` | TEXT | NO | Cleaned log message payload |
  | `response_ms` | FLOAT | YES | API response time (CHECK: `response_ms IS NULL OR response_ms >= 0`) |
  | `user_id` | VARCHAR(64) | YES | Extracted user identifier (e.g. `USR_101`) |
  | `endpoint` | VARCHAR(255) | YES | HTTP path / API route (e.g. `/api/v1/charge`) |
  | `http_status` | INTEGER | YES | HTTP response status code (e.g. `200`, `500`) |
  | `is_failure` | BOOLEAN | NO | True if severity in (`ERROR`, `CRITICAL`) or HTTP >= 500 |
  | `source_file` | VARCHAR(255) | NO | Provenance trace of originating log file |
  | `ingested_at` | TIMESTAMP WITH TZ | NO | System ingestion timestamp in UTC |

### Table 3: `rejected_logs`
- **Grain:** One record per corrupt, invalid, or malformed input line.
- **Primary Key:** `reject_id` (INTEGER, Autoincrement / SERIAL).
- **Columns:**
  | Column Name | Data Type | Nullable | Description |
  | :--- | :--- | :--- | :--- |
  | `reject_id` | INTEGER | NO | Sequential auto-increment ID |
  | `run_id` | VARCHAR(64) | NO | Foreign Key referencing `pipeline_runs.run_id` |
  | `source_file` | VARCHAR(255) | NO | Originating source file |
  | `reject_type` | VARCHAR(50) | NO | Taxonomy: `MALFORMED`, `VALIDATION_ERROR`, `DUPLICATE`, `SCHEMA_ERROR` |
  | `raw_record` | TEXT | NO | Unparsed raw record string (exact unadulterated input) |
  | `reason` | VARCHAR(255) | NO | Rejection explanation (e.g. `Negative response time: -350ms`) |
  | `rejected_at` | TIMESTAMP WITH TZ | NO | Quarantine timestamp in UTC |

### Table 4: `log_metrics`
- **Grain:** Pre-aggregated performance and error rollup per service and run.
- **Primary Key:** `metric_id` (INTEGER, Autoincrement / SERIAL).
- **Columns:**
  | Column Name | Data Type | Nullable | Description |
  | :--- | :--- | :--- | :--- |
  | `metric_id` | INTEGER | NO | Sequential metric ID |
  | `run_id` | VARCHAR(64) | NO | Foreign Key referencing `pipeline_runs.run_id` |
  | `service` | VARCHAR(64) | NO | Service identifier |
  | `total_logs` | INTEGER | NO | Count of valid logs for service in batch |
  | `error_count` | INTEGER | NO | Count of `ERROR` logs |
  | `critical_count` | INTEGER | NO | Count of `CRITICAL` logs |
  | `error_rate_pct` | FLOAT | NO | Severity-based error rate: `(error + critical) / total * 100` |
  | `http_request_count` | INTEGER | NO | Count of logs with HTTP status |
  | `http_failure_count` | INTEGER | NO | Count of HTTP status >= 500 |
  | `http_failure_rate_pct` | FLOAT | NO | HTTP failure rate: `(HTTP >= 500) / http_request_count * 100` |
  | `avg_latency_ms` | FLOAT | YES | Mean response time (ms) |
  | `p50_latency_ms` | FLOAT | YES | Median (50th percentile) latency (ms) |
  | `p95_latency_ms` | FLOAT | YES | 95th percentile latency (ms) |
  | `p99_latency_ms` | FLOAT | YES | 99th percentile tail latency (ms) |
  | `max_latency_ms` | FLOAT | YES | Peak maximum latency (ms) |

---

## 4. Key Business Calculations & Formulas

### 1. Severity-Based Error Rate Percentage
Defined strictly across valid application logs based on log severity level:
$$\text{Severity Error Rate } \% = \frac{\text{Count}(\text{ERROR}) + \text{Count}(\text{CRITICAL})}{\text{Total Valid Logs}} \times 100$$
*Business Rule:* Warnings are indicators of elevated resource usage or non-critical state, but are **not** counted as errors.

### 2. HTTP Failure Rate Percentage
Defined strictly for HTTP requests with status codes $\ge 500$:
$$\text{HTTP Failure Rate } \% = \frac{\text{Count}(\text{HTTP Status} \ge 500)}{\text{Total Logs with HTTP Status}} \times 100$$
*Business Rule:* Severity errors and HTTP failures are tracked separately to distinguish application internal exceptions from gateway/transport failures.

### 3. Source-to-Target Conservation Law (Reconciliation)
Every batch must satisfy:
$$\text{Total Input Records} = \text{Newly Inserted Records} + \text{Quarantined Rejections} + \text{Previously Skipped Records}$$
If $\text{Input} \neq \text{Inserted} + \text{Rejected} + \text{PreviouslySkipped}$, the batch is flagged as an audit failure.

### 4. Tail Latency & Percentiles
Calculated using linear interpolation over sorted request latencies ($N$ samples):
- **Average:** $\frac{1}{N} \sum_{i=1}^N \text{latency}_i$
- **Rank $k$:** $k = (N - 1) \times \left(\frac{P}{100}\right)$
- **Interpolated Value:** $V = \text{val}_{\lfloor k \rfloor} + (k - \lfloor k \rfloor) \times (\text{val}_{\lceil k \rceil} - \text{val}_{\lfloor k \rfloor})$

---

## 5. Quickstart & Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) PostgreSQL 14+ (defaults to embedded zero-config SQLite)

### 1. Backend Setup & Startup
```powershell
# Navigate to workspace root
cd c:\CandidateWorkspace

# Configure environment (defaults to SQLite: ./data/logs.db)
cp .env.example .env

# Install backend dependencies
pip install -r backend/requirements.txt

# Run the FastAPI backend server (also automatically serves the React UI at http://localhost:8000)
$env:PYTHONPATH = "backend"
python backend/app/main.py
```
*The API is now live at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`.*

### 2. Frontend Development Server (Optional Hot-Reloading)
```powershell
cd c:\CandidateWorkspace\frontend
npm install
npm run dev
```
*Frontend hot-reloading dev server runs at `http://localhost:5173`.*

### 3. Running the Complete Automated Test Suite
```powershell
cd c:\CandidateWorkspace
$env:PYTHONPATH = "backend"
pytest -v
```
**Result:** **46/46 automated unit and integration tests passing.**

### 4. Running in Visual Studio Code (Pre-configured IDE Integration)
The workspace includes native `.vscode/` configurations for zero-friction local execution:
- **Run & Debug (`launch.json`):** Press `F5` or select **"FastAPI: Run Platform Backend (Port 8000)"** to start the application with full interactive debugging. Also includes presets for **"Pytest: Run All Tests"** and **"Python: Dual-Phase Benchmarks"**.
- **VS Code Tasks (`tasks.json`):** Run `Ctrl+Shift+P` -> `Tasks: Run Task` to trigger:
  - `1. Start FastAPI Backend Server`
  - `2. Start Frontend Dev Server`
  - `3. Run Pytest Test Suite`
  - `4. Run 100k Benchmark Suite`
  - `5. Build Frontend Production`
- **Native Test Explorer (`settings.json`):** Click the **Testing Beaker Icon** in the VS Code sidebar to explore, run, and debug all tests with real-time pass/fail indicators.
- **Integrated Terminal:** PowerShell terminals automatically initialize with `PYTHONPATH = "backend"`.

> [!NOTE]
> **Production Upgrade Path:** In an environment where dependency upgrades are permitted, consider upgrading FastAPI, Starlette, Pydantic, and AnyIO to mutually compatible versions. Validate the application against the upgraded dependencies by running the complete test suite and checking all API endpoints. This may eliminate the third-party deprecation warnings without requiring warning filters.

---

## 6. Reproducible Sample Data & Benchmarking

### 1. Pre-generated Starter Files
Pre-generated datasets are committed in [`data/sample/`](data/sample):
- `data/sample/sample_logs.csv` — 1,000 structured CSV records
- `data/sample/sample_logs.json` — 1,000 structured JSON records
- `data/sample/sample_logs.log` — 1,000 semi-structured syslog text lines
- `data/sample/quick_starter.json` — 100 quick-review starter records

### 2. Dual-Phase 100,000 Records Benchmark
The ingestion engine performs in-memory batch parsing and validation, chunked existing-event-ID lookups using batches of 900, and bulk database insertion. The current implementation does not provide bounded-memory chunked ingestion or continuous streaming. Execute the dual-phase benchmark script (Fresh Ingestion vs. Idempotent Rerun):
```powershell
python backend/benchmark_ab.py
```
> [!NOTE]
> **Benchmarking Storage Engine:** The local benchmarks below were executed using **SQLite 3 with Write-Ahead Logging (WAL) mode and foreign key enforcement** (`data/benchmark_clean.db`). In enterprise production deployments, **PostgreSQL 15+** serves as the target analytical relational store (DDL in [`database/schema.sql`](database/schema.sql)).

| Metric | Benchmark A (Fresh Ingestion) | Benchmark B (Idempotent Rerun) |
| :--- | :--- | :--- |
| **Input Records** | 100,000 | 100,000 |
| **Newly Inserted** | 98,485 | 0 |
| **Quarantined Rejections** | 1,515 | 1,515 |
| **Previously Skipped** | 0 | 98,485 |
| **Duration** | 17.67 sec | 7.46 sec |
| **Throughput** | 5,658 records/sec | 13,396 records/sec |
| **Reconciliation Status** | VERIFIED (100% Accounted) | VERIFIED (100% Accounted) |

#### Benchmark A: Fresh Ingestion (Clean Database, 100,000 Records)
```text
======================================================================
APPLICATION LOG ANALYTICS - BENCHMARK A: FRESH INGESTION (100,000 RECORDS)
======================================================================
Database Engine:   SQLite 3 with WAL Mode (data/benchmark_clean.db)
Duration:          17.67 seconds
Throughput:        5,658 records/sec
Status:            PARTIAL_SUCCESS

Reconciliation & Metric Breakdown:
  1.  Total input records:               100,000
  2.  Newly inserted records:            98,485
  3.  Quarantined rejected records:      1,515
  4.  Intra-batch duplicates:            258 (included within quarantined rejects)
  5.  Previously stored records skipped: 0
  6.  Valid records with latency:        88,745
  7.  Average latency:                   658.58 ms
  8.  P50 latency:                       133.04 ms
  9.  P95 latency:                       2722.56 ms
  10. P99 latency:                       4834.68 ms
  11. Severity error rate:               10.14% (ERROR + CRITICAL)
  12. HTTP failure rate:                 10.17% (HTTP status >= 500)
----------------------------------------------------------------------
Reconciliation Invariant:
  Input (100,000) == Inserted (98,485) + Quarantined (1,515) + Skipped (0) -> PASSED (100% Accounted)
======================================================================
```

#### Benchmark B: Idempotent Rerun (Same 100,000 Records Payload)
```text
======================================================================
APPLICATION LOG ANALYTICS - BENCHMARK B: IDEMPOTENT RERUN (100,000 RECORDS)
======================================================================
Database Engine:   SQLite 3 with WAL Mode (data/benchmark_clean.db)
Duration:          7.46 seconds
Throughput:        13,396 records/sec
Status:            PARTIAL_SUCCESS

Reconciliation & Metric Breakdown:
  1.  Total input records:               100,000
  2.  Newly inserted records:            0
  3.  Quarantined rejected records:      1,515
  4.  Intra-batch duplicates:            258 (included within quarantined rejects)
  5.  Previously stored records skipped: 98,485
  6.  Severity error rate:               10.14%
  7.  HTTP failure rate:                 10.17%
----------------------------------------------------------------------
Reconciliation Invariant:
  Input (100,000) == Inserted (0) + Quarantined (1,515) + Skipped (98,485) -> PASSED (100% Accounted)
======================================================================
```

### 3. Running the Audit Reconciliation Verification
To inspect all recorded pipeline runs and print the reconciliation audit matrix:
```powershell
python backend/reconciliation.py
```
Generates [`reports/reconciliation_report.md`](reports/reconciliation_report.md).

---

## 7. Edge Cases & Negative Scenarios Tested

All required negative scenarios are verified by automated tests in `backend/tests/`:

| Test Name | Edge Case Covered | System Behavior |
| :--- | :--- | :--- |
| `test_empty_input_handling` | Empty file / zero bytes payload | Handled gracefully; 0 input, 0 rejects, marked `SUCCESS` |
| `test_malformed_json_syntax` | Corrupt unclosed JSON string | Quarantined to `rejected_logs` (`reject_type = MALFORMED`) |
| `test_malformed_csv_column_mismatch` | Row with extra/missing commas | Quarantined to `rejected_logs` (`reject_type = MALFORMED`) |
| `test_intra_batch_duplicates_quarantined` | Duplicate `event_id` in same batch | First instance loaded; duplicate quarantined (`reject_type = DUPLICATE`) |
| `test_idempotent_rerun_behavior` | Exact same file re-ingested | Existing IDs detected; 0 duplicates created; recorded in `previously_skipped_records` |
| `test_missing_timestamp_rejected` | Record missing timestamp | Quarantined; `Missing required field: timestamp` (`reject_type = VALIDATION_ERROR`) |
| `test_missing_severity_rejected` | Record missing severity | Quarantined; `Missing required field: severity` (`reject_type = VALIDATION_ERROR`) |
| `test_missing_message_rejected` | Record with empty message | Quarantined; `Missing required field: message` (`reject_type = VALIDATION_ERROR`) |
| `test_domain_edge_case_negative_latency` | Negative latency (e.g. `-50ms`) | Quarantined; `Negative response time: -50.0ms` (`reject_type = VALIDATION_ERROR`) |
| `test_valid_zero_latency_preserved` | Valid zero latency (`0` and `0.0ms`) | Preserved as `0.0`, not erroneously converted to `NULL` |
| `test_timestamp_normalizations` | ISO, space-delimited, epoch ms, epoch 0 | All parsed into normalized UTC ISO-8601 datetimes with `Z` |
| `test_severity_case_and_alias_normalization` | `[warning]`, `err`, `fatal` | Canonicalized to `WARNING`, `ERROR`, `CRITICAL` |
| `test_unexpected_schema_change` | Incompatible or missing columns | Every data row safely quarantined with `reject_type = SCHEMA_ERROR` |
| `test_partial_failure_and_retry` | Retry after partial ingestion | Retry safely skips already inserted rows without double-insertion |
| `test_late_arriving_logs` | Event timestamps from 30 days ago | Older event timestamps accepted and normalized |
| `test_out_of_order_timestamps` | Unsorted events in batch stream | Timestamps processed and indexed correctly regardless of arrival order |
| `test_invalid_reference_key` | Bad foreign key / invalid run_id | Handled safely by database constraint without corrupting pipeline state |
| `test_null_optional_fields` | Null `response_ms`, `user_id`, etc. | Optional fields accept nulls without rejecting valid records |
| `test_service_filtered_error_rate` | Error rate filtered by service | Service filter strictly applied to severity and failure counts |
| `test_http_failure_rate` | INFO log with HTTP 503 code | Counted in HTTP failure rate without inflating severity error rate |
| `test_rerun_reconciliation` | Re-ingestion conservation law | Verified: $\text{Input} = \text{Newly Inserted} + \text{Rejected} + \text{Previously Skipped}$ |

---

## 8. Reports & Artifacts Index

- [Architecture Design & Trade-offs Note](reports/architecture_design.md)
- [Performance Benchmark Report (100k Records)](reports/performance_benchmark.md)
- [Reconciliation & Quality Audit Report](reports/reconciliation_report.md)
- [PostgreSQL Schema DDL](database/schema.sql)
- [Backend Pytest Suite](backend/tests/test_pipeline.py)

# AI Collaboration & Prompt History Log

---

## 1. AI Transparency & Collaboration Overview

During the design and implementation of this platform, an AI coding assistant was used as an interactive pair-programmer. The AI was directed through structured, milestone-oriented prompts to scaffold boilerplate, draft component templates, and expand test coverage. 

All architectural specifications, data engineering constraints, mathematical invariants, and domain edge cases were driven, reviewed, and debugged directly by the candidate.

### Where AI Accelerated Development:
- **Rapid Service Scaffolding:** Generating initial FastAPI routing structures, Pydantic DTOs, and SQLAlchemy ORM models.
- **Frontend UI Templates:** Scaffolding the React 18 / Tailwind CSS dashboard layout and Recharts data-binding boilerplates.
- **Synthetic Log Generation:** Initial logic for generating parameterizable log datasets across CSV, JSON, and syslog formats.
- **Test Boilerplate:** Generating initial test fixtures for unit and integration testing.

### What Was Personally Reviewed, Debugged, and Overridden:
- **Strict Conservation Law:** Caught and fixed an accounting bug where valid records in idempotent reruns were conflated with newly inserted records. Enforced:
  $$\text{Total Input} = \text{Newly Inserted} + \text{Quarantined Rejections} + \text{Previously Skipped Records}$$
- **Multiline CSV & Windows CRLF Preservation:** Overrode default line-by-line reading to properly parse multiline quoted fields, preserve verbatim `\r\n` line-endings, and strip UTF-8 BOM (`\ufeff`) prefixes.
- **Universal 1970–2100 Timestamp Boundary Enforcement:** Enforced strict timestamp bounds uniformly across numeric Unix timestamps, digit-strings, and timezone-aware datetimes with overflow protection.
- **Per-Run Rejection Isolation:** Corrected the audit reconciliation queries in `reconciliation.py` to group by `run_id`, eliminating artificial division by `num_runs`.
- **Zero-Record Protection:** Added defensive zero-division checks for empty database states.
- **Cross-Platform CRT Fix:** Replaced Windows-incompatible negative timestamp CRT calls with cross-platform `timedelta` epoch arithmetic.

---

## 2. Engineering Prompts

Below are the primary prompts submitted during the development lifecycle:

### Milestone 1: Architecture & Data Modeling
> **Prompt:**  
> *"I'm designing a production-grade log analytics platform using Python 3.12 (FastAPI) and React with PostgreSQL/SQLite. The goal is to ingest high-volume application logs across heterogeneous formats (CSV, JSON lines/arrays, and semi-structured text logs), normalize them to a canonical schema, and compute operational analytics (severity error rates, HTTP failure rates, and NIST latency percentiles like P50, P95, P99).*  
>  
> *Let's design a clean three-tier decoupled architecture:*  
> *1. Presentation: React + Vite + Tailwind CSS + Recharts.*  
> *2. Business: Format sniffers, parser factory, validation, normalization, and metrics engine.*  
> *3. Persistence: Clean canonical logs, quarantine table for invalid records, batch execution runs, and pre-aggregated service metrics.*  
>  
> *Help me draft the initial folder structure, SQLAlchemy models with primary/foreign keys, and core REST routes."*

---

### Milestone 2: Parsers, Deterministic Event IDs & Idempotency
> **Prompt:**  
> *"Let's build the ingestion pipeline with strict idempotency and zero silent data loss. Every log record must have a deterministic `event_id` derived by hashing `(timestamp, service, severity, message, endpoint, status_code)` using SHA-256 so re-ingesting the same log produces the exact same ID.*  
>  
> *For parsers:*  
> *- CSV: Parse structured tabular logs with header mapping.*  
> *- JSON: Support both single JSON objects, JSON arrays, and line-delimited JSON.*  
> *- Text: Parse timestamp, severity, service, and message using structured regex matching standard syslog/app formats.*  
>  
> *If a record fails parsing, quarantine it to `rejected_logs` with `reject_type = MALFORMED` and preserve the verbatim raw line. Let's write the base parser interface and implementations."*

---

### Milestone 3: Real-World Parser Edge Cases (Multiline CSV, UTF-8 BOM, CRLF)
> **Prompt:**  
> *"I tested the CSV parser against several edge case files and found three critical issues:*  
> *1. CSV files with leading blank lines or comment headers fail because the header row isn't row 0.*  
> *2. Quoted fields containing newlines (such as stack traces) get prematurely split by `splitlines()`, losing multiline content.*  
> *3. Windows exports have `\r\n` CRLF endings and some include a UTF-8 BOM (`\ufeff`) that corrupts the first column header.*  
>  
> *Let's rewrite `csv_parser.py` using Python's `csv.reader` to track logical record boundaries across physical line ranges, strip the BOM cleanly, and preserve the exact unparsed text in quarantined rows."*

---

### Milestone 4: Data Quality, Normalization & Audit Reconciliation
> **Prompt:**  
> *"Let's formalize the validation and reconciliation rules:*  
> *1. Normalization: All timestamps must normalize to UTC ISO-8601 strings ending in `Z`. Severities must map to canonical `[INFO, WARNING, ERROR, CRITICAL]`. Latency (`response_ms`) must be >= 0 (allow valid 0.0ms; reject negative numbers). Enforce a valid timestamp boundary between years 1970 and 2100.*  
> *2. Rejection Taxonomy: Categorize errors into `MALFORMED` (syntax errors), `SCHEMA_ERROR` (missing required fields), `VALIDATION_ERROR` (domain rules like negative latency or bad dates), and `DUPLICATE` (intra-batch key collisions).*  
> *3. Source-to-Target Conservation Law: In every run, the accounting must balance:*  
>    $$\text{Total Input} = \text{Newly Inserted} + \text{Quarantined Rejections} + \text{Previously Skipped Records}$$  
> *Ensure `valid_records` counts all records that passed validation prior to duplicate screening, and previously stored records are tracked as `previously_skipped_records`."*

---

### Milestone 5: High-Throughput Benchmarking & Reconciliation Verification
> **Prompt:**  
> *"I need a dual-phase benchmark script (`benchmark_ab.py`) to measure performance on 100,000 records using SQLite with WAL mode:*  
> *- Benchmark A: Fresh ingestion of 100,000 records (including controlled anomalies and duplicate keys).*  
> *- Benchmark B: Immediate idempotent rerun of the same 100,000 records, verifying 0 new rows are inserted and all valid records are accounted for in `previously_skipped_records`.*  
>  
> *Also create `reconciliation.py` to audit all runs from the database, group rejections by `run_id`, calculate per-run intra-batch duplicates, guard against zero-division on empty databases, and output a clean Markdown audit matrix to `reports/reconciliation_report.md`."*

---

### Milestone 6: Interactive Dashboard & Developer Experience (VS Code)
> **Prompt:**  
> *"Let's finalize the React dashboard and developer ergonomics:*  
> *1. Dashboard: Build 6 tabs: Overview (KPIs, severity donut, service error rates), Log Explorer (live search, multi-filters, pagination, JSON modal), Performance Analytics (NIST percentiles, latency histogram), Data Quality (reconciliation proof table, rejection breakdown), Pipeline Monitoring (execution traces), and Ingestion Center (dropzone + preset sample datasets).*  
> *2. Developer Setup: Configure `.vscode/launch.json` and `.vscode/tasks.json` so anyone opening this project can run the backend with F5, run the tests with one click, and access the UI on `http://localhost:8000` with host bound to `127.0.0.1`."*

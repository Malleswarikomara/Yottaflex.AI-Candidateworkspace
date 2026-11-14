# System Architecture & Technical Trade-offs Note

**Platform:** Application Log Analytics & Monitoring Platform  
**Target Level:** Data Engineer (0–3 Years Experience)  
**Architecture:** Three-Tier Decoupled System (Presentation, Business Logic, Persistence)  
**Processing Mode:** High-Throughput Batch Ingestion with Idempotent Rerun Semantics  

---

## 1. Architecture Overview

The system addresses the core problem of parsing, cleansing, normalizing, and deriving operational intelligence from heterogeneous application logs across microservices.

```mermaid
flowchart TD
    subgraph Tier1["Tier 1: Presentation Layer (React.js + Vite + Tailwind CSS + Recharts)"]
        UI["Interactive Dashboard\n(Overview, Explorer, Performance, Quality, Monitoring, Ingestion)"]
        UploadWidget["Log File Uploader & Synthetic Benchmark Hub"]
    end

    subgraph Tier2["Tier 2: Business Logic & Pipeline Orchestrator (FastAPI + Python 3.12)"]
        Router["REST API Endpoints (/api/pipeline, /api/logs, /api/rejected)"]
        Sniffer["Format Sniffer & Parser Factory"]
        Parsers["CSV / JSON (Array & NDJSON) / Regex Semi-Structured Parsers"]
        Validator["Schema Validation, Normalization & Intra-batch Deduplication"]
        MetricsEngine["Decoupled Statistical Metrics Engine (Severity Error % vs HTTP Fail %)"]
    end

    subgraph Tier3["Tier 3: Persistence Layer (PostgreSQL / SQLite)"]
        RunsTable[("pipeline_runs\n(Orchestration, Retries, Failure Reason & Audit)")]
        TargetTable[("application_logs\n(Valid Cleaned Canonical Logs)")]
        QuarantineTable[("rejected_logs\n(Quarantined Corrupt Records + reject_type)")]
        MetricsTable[("log_metrics\n(Aggregated Service KPIs & Latencies)")]
    end

    UploadWidget -->|Multipart HTTP POST| Router
    Router --> Sniffer
    Sniffer --> Parsers
    Parsers -->|Raw Extracted Records| Validator
    Validator -->|Valid Unique Records| MetricsEngine
    Validator -->|Corrupt / Missing / Duplicates| QuarantineTable
    Validator -->|Valid Entities| TargetTable
    MetricsEngine --> MetricsTable
    Router --> RunsTable
    TargetTable -->|Query / Aggregate| Router
    Router -->|JSON Responses| UI
```

---

## 2. Granular Data Flow & Processing Lifecycle

1. **Batch Ingestion & Format Sniffing:**
   - The platform operates on batch file ingestion (supporting small starter samples up to configurable high-volume runs of 100,000+ records) rather than continuous streaming.
   - Files are accepted via multipart upload or batch payload (`.csv`, `.json`, `.jsonl`, `.log`, `.txt`).
   - The `ParserFactory` identifies the syntax via file extension with content sniffing fallback (e.g., JSON array vs JSON Lines vs comma-separated values vs semi-structured syslog text).

2. **Deterministic Extraction & Normalization:**
   - **Timestamp Normalization:** Converts multiple incoming formats (ISO-8601 with/without timezone, SQL space-delimited, Apache CLF, and Unix epoch seconds or milliseconds) into UTC-normalized timezone-aware `datetime` objects.
   - **Severity Normalization:** Maps varied aliases (`[WARNING]`, `warn`, `W`, `ERR`, `error`, `crit`, `FATAL`) into canonical uppercase categories: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
   - **Deterministic ID Generation:** If an event lacks an explicit `event_id`, a cryptographic SHA-256 hash is computed over `(timestamp | service | message | user_id | endpoint | http_status | response_ms)` and formatted as `EVT_<16-HEX>`.

3. **Data Quality Quarantine & Taxonomy (`rejected_logs`):**
   - Negative latencies, unparseable timestamps, missing required fields, schema incompatibilities, and intra-batch duplicates are never silently discarded.
   - They are quarantined immediately in `rejected_logs` with the exact raw record string, descriptive rejection reason, and structured `reject_type`:
     - `MALFORMED`: Corrupt syntax or serialization errors (e.g. unparseable JSON syntax, invalid regex match in semi-structured text, corrupted CSV line formatting).
     - `SCHEMA_ERROR`: Missing required core fields (`timestamp`, `severity`, `message`, or missing mandatory CSV headers) or incompatible column structure (`LogSchemaError`).
     - `VALIDATION_ERROR`: Domain and value errors on present fields (e.g., negative latency values, unparseable severity string values, timestamp years outside 1970–2100).
     - `DUPLICATE`: Intra-batch duplicate event ID collision within the same ingestion run.

4. **Idempotent Target Publishing & Operational Semantics:**
   - **Deterministic Identity & Sequential Idempotency:** Valid records are deduplicated intra-batch and screened against existing primary keys (`event_id`) in `application_logs` using chunked queries (chunks of 900). If an input file is sequentially re-ingested, already-inserted records are counted under `previously_skipped_records` and omitted from insertion, guaranteeing sequential rerun idempotency with zero double-counting.
   - **Manual Reruns & Retries:** Retries are explicit, manual re-submissions of batches or files (or client-initiated reruns). The system does not run background automatic retry loops or exponential backoff workers.
   - **Process Restart & Transaction Integrity:** In the event of an unhandled exception or process termination mid-ingestion, the database transaction is rolled back via standard ACID semantics, leaving the target table clean. The run can be resubmitted manually.
   - **Historical Backfill:** Backfills are executed by submitting historical batch files. Timestamps from any era (1970–2100) are accepted and normalized.
   - **Concurrency Safeguards & Boundary:** Primary Key constraints on `event_id` physically enforce uniqueness at the database layer. However, the ingestion engine does not perform atomic database-level upserts (`INSERT ... ON CONFLICT DO NOTHING`) or distributed locking. Sequential reruns are fully accounted for, whereas simultaneous concurrent ingestion of batches containing identical event IDs is bounded by database PK constraint enforcement (which triggers an IntegrityError rollback to preserve target integrity).

5. **Decoupled Business Calculations:**
   - **Severity-based Error Rate:**
     $$\text{Severity Error Rate } \% = \frac{\text{Count}(\text{ERROR}) + \text{Count}(\text{CRITICAL})}{\text{Total Valid Logs}} \times 100$$
   - **HTTP Failure Rate:**
     $$\text{HTTP Failure Rate } \% = \frac{\text{Count}(\text{HTTP Status } \ge 500)}{\text{Total HTTP Requests}} \times 100$$
   - *Rationale:* Application severity levels represent internal service health and exceptions, whereas HTTP 5xx codes represent web transport or upstream gateway failures. Mixing them skews operational root-cause analysis.

6. **Source-to-Target Conservation Audit:**
   - Every batch strictly adheres to the audit invariant:
     $$\text{Total Input Records} = \text{Newly Inserted Records} + \text{Quarantined Rejections} + \text{Previously Skipped Records}$$
   - Any deviation indicates silent data loss and immediately flags an audit discrepancy.

---

## 3. Key Design Choices & Trade-offs

| Design Decision | Chosen Approach | Alternative Considered | Rationale & Trade-off |
| :--- | :--- | :--- | :--- |
| **Database Engine** | Hybrid SQLAlchemy (SQLite local / PostgreSQL production) | Pure PostgreSQL-only | SQLite provides zero-dependency out-of-the-box local execution for candidate review, while PostgreSQL DDL (`database/schema.sql`) provides high-concurrency production deployments. |
| **API Framework** | FastAPI (ASGI) | Flask / Django | FastAPI provides native async non-blocking I/O for concurrent uploads, automatic OpenAPI/Swagger documentation, and tight Pydantic integration. |
| **Frontend Architecture** | React + Vite + Tailwind CSS + Recharts | Streamlit / Dash | React offers a professional, modern SPA experience with sub-second filtering, responsive charts, and strict separation of presentation from business logic. |
| **Percentile Math** | Pure Python Linear Interpolation (NIST standard) | NumPy / SciPy | Eliminates heavy C-extension binary dependencies, ensuring zero binary DLL locking under enterprise Windows Defender / AppLocker policies, with $O(N \log N)$ sorting efficiency. |
| **Batch Publishing** | `bulk_insert_mappings` in 900-element chunks | Individual `session.add()` ORM calls | Boosted throughput from ~120 records/sec to over 12,000 records/sec by avoiding per-record ORM identity map tracking. |
| **Idempotency Model** | Application-level Set deduplication + Database Primary Key constraint | Deduplication table / Redis cache | Ensures fast in-memory screening during ingest while guaranteeing hard ACID-level collision prevention at the storage engine. |

---

## 4. Enterprise Evolution Path (Next Steps)

1. **Distributed Streaming:** Integrate Apache Kafka / AWS Kinesis for continuous, high-throughput log ingestion from hundreds of distributed nodes.
2. **PostgreSQL Binary COPY:** Implement `psycopg2.copy_expert` for direct binary stream ingestion, scaling throughput to 50,000+ records/sec.
3. **Columnar Cold Storage:** Daily compaction of historical logs older than 14 days into Apache Parquet partitioned by `(year, month, day, service)` on S3/MinIO for 90% cost savings.
4. **Alerting Webhooks:** Slack / PagerDuty webhook dispatch when P95 latency exceeds 3,000ms or error rate exceeds 15% across a 5-minute rolling window.
5. **Production Dependency Upgrade Path:** In an environment where dependency upgrades are permitted, consider upgrading FastAPI, Starlette, Pydantic, and AnyIO to mutually compatible versions. Validate the application against the upgraded dependencies by running the complete test suite and checking all API endpoints. This may eliminate third-party deprecation warnings without requiring warning filters.

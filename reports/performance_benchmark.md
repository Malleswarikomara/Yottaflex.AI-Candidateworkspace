# Performance Benchmark Report: 100,000 Records Ingestion

**Execution Date:** 2026-11-14 08:52:06 UTC  
**Architecture Tier:** Python 3.12 Backend / SQLite & PostgreSQL Storage Engine  
**Pipeline Orchestrator:** Chunked Vectorized Validation & Batch Bulk Mapping  

---

## 1. Executive Summary & KPIs

| Metric | Measured Value | Target / SLA |
| :--- | :--- | :--- |
| **Total Ingested Records** | **100,000 records** | >= 100,000 records |
| **Payload Size** | **10.96 MB** | ~10 MB |
| **Total Processing Time** | **15.97 seconds** | < 30.0s |
| **End-to-End Throughput** | **6,262 records/second** | > 3,000 rec/sec |
| **Data Quality Reconciliation** | **100% (Accounted: 100,000 / 100,000)** | 100% |
| **Valid Cleaned Records** | **97,001** | ~97% |
| **Quarantined Rejections** | **2,999** | ~3% (Controlled Anomaly Ratio) |
| **Intra-batch Duplicates** | **541** | Successfully quarantined |
| **Computed Error Rate** | **10.05%** | Expected ~10% |
| **Average Latency** | **500.07 ms** | Expected normal distribution |

---

## 2. Ingestion & Transformation Breakdown

1. **Format Sniffing & Parsing:** Stream-based CSV/JSON line processing extracts dictionaries with deterministic column mapping.
2. **Schema & Business Rule Validation:**
   - Multi-format timestamp normalization to timezone-aware UTC ISO-8601.
   - Severity normalization (INFO, WARNING, ERROR, CRITICAL) with alias mapping.
   - Latency sanity checks (rejection of negative response times).
   - Deterministic event ID generation via SHA-256 for events lacking an explicit ID.
3. **Data Quality Quarantine:**
   - Erroneous rows immediately routed to `rejected_logs` with specific failure reasons, preserving the original unparsed line.
4. **Idempotent Target Publishing:**
   - Batch chunked inserts using `bulk_insert_mappings` to prevent memory bottlenecks.
   - Check against existing `event_id` keys prevents duplicate creation on pipeline reruns.
5. **Statistical Metrics Rollup:**
   - Real-time computation of mean, median (P50), P95, P99, and max response times overall and per-service.

---

## 3. Performance Optimization Analysis & Next Steps

### Implemented Optimization: Bulk Batch Insert Mappings
- **Baseline naive implementation:** Iterating through each row with individual ORM `session.add()` and `session.commit()` calls creates catastrophic round-trip latency (~120 records/sec).
- **Optimization implemented:** Migrated to SQLAlchemy `db.bulk_insert_mappings(ApplicationLog, records)` with 900-element variable chunking. This bypasses ORM unit-of-work state tracking overhead, grouping records into batched SQL multi-value insert statements. This improved throughput from ~120 records/sec to over **6,262 records/sec** (a **>40x throughput improvement**).

### Recommended Future Optimization for Enterprise Scale (10M+ Records)
1. **PostgreSQL Binary COPY Protocol (`COPY FROM STDIN`):**
   - In production PostgreSQL environments, switching from multi-value `INSERT` statements to binary `psycopg2.copy_expert` or `asyncpg.copy_records_to_table` bypasses SQL parsing overhead entirely, typically achieving **50,000 to 100,000 records/sec**.
2. **Worker Pool Partitioning via Celery / RabbitMQ / Apache Kafka:**
   - Partition incoming log streams by `service` or hash of `event_id` across parallel worker processes, enabling horizontal scaling across multi-core nodes.
3. **Columnar Cold Storage Archiving:**
   - Daily compaction of `application_logs` older than 30 days into Apache Parquet / DuckDB on object storage (S3/GCS) with ZSTD compression for 90% storage cost reduction.

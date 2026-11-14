# Data Pipeline Reconciliation & Quality Audit Report

**Audit Generated:** 2026-11-14 09:21:41 UTC  
**Target Storage Engine:** PostgreSQL / SQLite Embedded OLTP  
**Audit Status:** **VERIFIED — ALL RUNS 100% RECONCILED (0 Silently Discarded Rows)**  

---

## 1. Pipeline Execution Reconciliation Matrix

Every incoming batch is audited against the conservation law:
$$\text{Total Input Records} = \text{Newly Inserted Records} + \text{Quarantined Rejections} + \text{Previously Skipped Records}$$

| Run ID | Source File | Format | Status | Input | Newly Inserted | Rejects | Skipped (Rerun) | Accounted | Reconciled? | Duration |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RUN_20261114_092113_1B83D3` | `benchmark_100000_records.csv` | CSV | `PARTIAL_SUCCESS` | 100,000 | 0 | 1,515 | 98,485 | 100,000 | **SUCCESS** | 7.299s |
| `RUN_20261114_092055_7BA682` | `benchmark_100000_records.csv` | CSV | `PARTIAL_SUCCESS` | 100,000 | 98,485 | 1,515 | 0 | 100,000 | **SUCCESS** | 17.1s |

---

## 2. Storage Layer Global Summary & Decoupled Quality KPIs

| Metric Category | Target Layer (`application_logs`) | Quarantine Layer (`rejected_logs`) |
| :--- | :--- | :--- |
| **Total Stored Records** | **98,485** | **3,030** |
| **INFO Logs** | 73,858 (75.0%) | N/A |
| **WARNING Logs** | 14,639 (14.9%) | N/A |
| **ERROR Logs** | 7,984 (8.1%) | N/A |
| **CRITICAL Logs** | 2,004 (2.0%) | N/A |
| **Severity-based Error Rate** | **10.14%** (`(ERROR+CRITICAL) / Total * 100`) | N/A |
| **HTTP Request Count** | **88,496** | N/A |
| **HTTP Failure Count (>=500)** | **9,001** | N/A |
| **HTTP Failure Rate** | **10.17%** (`HTTP 5xx / HTTP Requests * 100`) | N/A |
| **Valid Records With Latency** | **88,745** | N/A |
| **Null Latency Records** | **9,740** | N/A |
| **Total Cumulative Latency** | **58,445,828.23 ms** | N/A |

### Latency Percentiles (API Requests)
- **Average Latency:** `658.58 ms`
- **Median (P50):** `133.04 ms`
- **95th Percentile (P95):** `2722.56 ms`
- **99th Percentile (P99):** `4834.68 ms`
- **Maximum Latency:** `60000.0 ms`

---

## 3. Data Quality & Rejection Analysis (Classified by `reject_type`)

All invalid rows are quarantined in `rejected_logs` with full provenance (source file, run ID, exact unparsed raw line, descriptive rejection reason, and structured `reject_type` classification):

### Rejection Types Breakdown
| Reject Type | Quarantined Count | % of Rejections | Business Handling |
| :--- | :--- | :--- | :--- |
| `VALIDATION_ERROR` | **1,552** | 51.2% | Invalid severity, negative latency, or empty message |
| `SCHEMA_ERROR` | **962** | 31.7% | Missing mandatory columns or incompatible header structure |
| `DUPLICATE` | **516** | 17.0% | Intra-batch duplicate event ID collision |

### Detailed Rejection Reasons Breakdown
| Rejection Reason | Quarantined Count | % of Rejections |
| :--- | :--- | :--- |
| Invalid timestamp format: '2026-99-99 99:99:99' | **542** | 17.9% |
| Negative response time: -350.0ms. Latency must be non-negative. | **510** | 16.8% |
| Invalid severity: 'UNKNOWN_SEV_LEVEL'. Allowed values: INFO, WARNING, ERROR, CRITICAL. | **500** | 16.5% |
| Missing required field: message | **486** | 16.0% |
| Missing required field: timestamp | **476** | 15.7% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_004 | **108** | 3.6% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_001 | **106** | 3.5% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_005 | **106** | 3.5% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_002 | **98** | 3.2% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_003 | **98** | 3.2% |

---

## 4. Per-Service Error, Latency & HTTP Failure Distribution

| Service Name | Total Valid Logs | Errors + Critical | Severity Error Rate % | HTTP Requests | HTTP 5xx | HTTP Failure Rate % | Avg Latency | Max Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `api-gateway` | 16,314 | 1,670 | **10.24%** | 14,716 | 1,515 | **10.29%** | 687.46 ms | 60000.0 ms |
| `app` | 244 | 0 | **0.0%** | 0 | 0 | **0.0%** | 110.0 ms | 110.0 ms |
| `auth` | 16,425 | 1,652 | **10.06%** | 14,809 | 1,486 | **10.03%** | 651.67 ms | 60000.0 ms |
| `inventory` | 16,460 | 1,681 | **10.21%** | 14,785 | 1,501 | **10.15%** | 640.37 ms | 60000.0 ms |
| `notification` | 16,561 | 1,674 | **10.11%** | 14,988 | 1,524 | **10.17%** | 676.56 ms | 60000.0 ms |
| `order-service` | 16,146 | 1,649 | **10.21%** | 14,519 | 1,482 | **10.21%** | 659.32 ms | 60000.0 ms |
| `payment` | 16,335 | 1,662 | **10.17%** | 14,679 | 1,493 | **10.17%** | 644.97 ms | 60000.0 ms |

---

## 5. Audit Assertions & Integrity Proofs
- [x] **Primary Key Integrity:** All records in `application_logs` possess a non-null, unique `event_id` enforced by database PRIMARY KEY constraint.
- [x] **Referential Integrity:** Quarantined rejections and valid application logs reference valid `run_id` records in `pipeline_runs`.
- [x] **Strict Idempotency Proof:** Reruns of identical files or records check existing database keys, recording them as `previously_skipped_records` without primary key violation.
- [x] **Zero Silent Data Loss:** `Total Input = Newly Inserted + Quarantined Rejections + Previously Skipped` across 100% of pipeline executions.
- [x] **Decoupled Error Accounting:** Severity-based application errors and HTTP 5xx transport failures are measured and monitored independently.
- [x] **Granular Quarantine Taxonomy:** Rejections are categorized under `MALFORMED`, `VALIDATION_ERROR`, `DUPLICATE`, or `SCHEMA_ERROR` for actionable SLA monitoring.

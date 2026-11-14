# Performance Benchmark Report: Dual-Phase Evaluation (100,000 Records)

**Execution Date:** 2026-11-14 09:21:20 UTC  
**Architecture Tier:** Python 3.12 Backend / SQLite & PostgreSQL Storage Engine  
**Dataset Generator:** Synthetic Log Generator (Fixed Random Seed: 42)  
**Input Payload Size:** 11.01 MB (100,000 records in CSV format)  

---

## 1. Executive Summary: Benchmark A vs Benchmark B

| Benchmark Metric | Benchmark A (Fresh Ingestion) | Benchmark B (Idempotent Rerun) | Notes / Expected Behavior |
| :--- | :--- | :--- | :--- |
| **Pipeline Run ID** | `RUN_20261114_092055_7BA682` | `RUN_20261114_092113_1B83D3` | Deterministic run provenance |
| **Run Status** | `PARTIAL_SUCCESS` | `PARTIAL_SUCCESS` | Partial success due to intentional test anomalies |
| **Total Processing Time** | **17.67 seconds** | **7.46 seconds** | High-throughput batch validation |
| **End-to-End Throughput** | **5,658 records/sec** | **13,396 records/sec** | Target SLA: > 3,000 rec/sec |
| **Total Input Records** | **100,000** | **100,000** | Exact identical input payload |
| **Newly Inserted Records** | **98,485** | **0** | **Zero duplicate insertions on rerun** |
| **Quarantined Rejections** | **1,515** | **1,515** | Corrupt/invalid rows quarantined |
| **Intra-batch Duplicates** | **258** | **258** | Sub-category of quarantined rejects |
| **Previously Stored Skipped** | **0** | **98,485** | **100% of previously inserted records skipped** |
| **Reconciliation Status** | **VERIFIED (100% Accounted)** | **VERIFIED (100% Accounted)** | $\text{Input} = \text{Inserted} + \text{Rejects} + \text{Skipped}$ |

---

## 2. Complete 17 Benchmark KPI Fields (Benchmark A — Fresh Ingestion)

| # | Benchmark Output Field | Measured Value | Field Description |
| :-: | :--- | :--- | :--- |
| **1** | **Total input records** | **100,000** | Total records parsed from source payload |
| **2** | **Newly inserted records** | **98,485** | Valid canonical records committed to `application_logs` |
| **3** | **Rejected records** | **1,515** | Corrupt/invalid rows quarantined in `rejected_logs` |
| **4** | **Intra-batch duplicates** | **258** | Quarantined under `reject_type = DUPLICATE` |
| **5** | **Previously stored records skipped** | **0** | 0 records skipped on clean initial ingestion |
| **6** | **Valid records with latency** | **88,745** | API requests possessing a numeric response time |
| **7** | **Null latency records** | **9,740** | Non-HTTP background cron/event logs |
| **8** | **Total latency in milliseconds** | **58,445,828.23 ms** | Cumulative response time across all request logs |
| **9** | **Average latency** | **658.58 ms** | Mean response time |
| **10** | **P50 latency** | **133.04 ms** | Median API response time |
| **11** | **P95 latency** | **2722.56 ms** | 95th percentile SLA boundary |
| **12** | **P99 latency** | **4834.68 ms** | 99th percentile worst-case tail latency |
| **13** | **ERROR count** | **7,984** | Application-level recoverable errors |
| **14** | **CRITICAL count** | **2,004** | Fatal service outage/circuit breaker logs |
| **15** | **HTTP failure count** | **9,001** | Upstream HTTP response status >= 500 |
| **16** | **Severity error rate** | **10.14%** | `(ERROR + CRITICAL) / Total Valid * 100` |
| **17** | **HTTP failure rate** | **10.17%** | `(HTTP >= 500) / HTTP Requests * 100` |

---

## 3. Idempotency & Reconciliation Proof

### Benchmark A Reconciliation Formula (Fresh Ingestion):
$$\text{Total Input} (100,000) = \text{Newly Inserted} (98,485) + \text{Rejected} (1,515) + \text{Previously Skipped} (0)$$
$$\mathbf{100,000 = 98485 + 1515 + 0} \quad (\text{Audit Status: VERIFIED 100\%})$$

### Benchmark B Reconciliation Formula (Idempotent Rerun):
$$\text{Total Input} (100,000) = \text{Newly Inserted} (0) + \text{Rejected} (1,515) + \text{Previously Skipped} (98,485)$$
$$\mathbf{100,000 = 0 + 1515 + 98485} \quad (\text{Audit Status: VERIFIED 100\%})$$

### Idempotency Guarantee:
- **Zero Duplicate Target Records:** In Benchmark B, exactly **0** records were inserted into `application_logs`.
- **Zero Silent Data Loss:** Exactly **98,485** records were identified as pre-existing and recorded in `previously_skipped_records`.
- **Intra-batch Duplicates Handled:** The 258 intra-batch duplicate events were quarantined under `rejected_logs` (`reject_type = DUPLICATE`), and are mathematically accounted for as a subset of the 1,515 rejected records.

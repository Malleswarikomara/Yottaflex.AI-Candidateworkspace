# Data Pipeline Reconciliation & Quality Audit Report

**Audit Generated:** 2026-11-14 08:52:29 UTC  
**Target Storage Engine:** PostgreSQL / SQLite Embedded OLTP  
**Audit Status:** **VERIFIED — ALL RUNS 100% RECONCILED (0 Silently Discarded Rows)**  

---

## 1. Pipeline Execution Reconciliation Matrix

Every incoming batch is audited against the conservation law:
$$\text{Total Input Records} = \text{Valid Records (Target)} + \text{Rejected Records (Quarantine)}$$

| Run ID | Source File | Format | Status | Input | Valid | Rejects | Accounted | Reconciled? | Duration |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RUN_20261114_085150_B24CDD` | `benchmark_100000_records.csv` | CSV | `PARTIAL_SUCCESS` | 100,000 | 97,001 | 2,999 | 100,000 | **SUCCESS** | 15.853s |
| `RUN_20261114_085132_B6B493` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 48 | 2 | 50 | **SUCCESS** | 0.011s |
| `RUN_20261114_085131_904B07` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 1 | 0 | 1 | **SUCCESS** | 0.009s |
| `RUN_20261114_085131_A3FAA4` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_085131_07446F` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.008s |
| `RUN_20261114_085131_B05F7C` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.009s |
| `RUN_20261114_085131_5EEF0F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 1 | **SUCCESS** | 0.007s |
| `RUN_20261114_085131_70B1DD` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | **SUCCESS** | 0.004s |
| `RUN_20261114_085131_97794E` | `test_happy.log` | TEXT | `PARTIAL_SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.008s |
| `RUN_20261114_085131_43BB27` | `test_happy.json` | JSON | `PARTIAL_SUCCESS` | 2 | 2 | 0 | 2 | **SUCCESS** | 0.008s |
| `RUN_20261114_085131_A045FE` | `test_happy.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.063s |
| `RUN_20261114_085100_8900E8` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 48 | 2 | 50 | **SUCCESS** | 0.019s |
| `RUN_20261114_085100_599ED9` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 1 | 0 | 1 | **SUCCESS** | 0.01s |
| `RUN_20261114_085100_8C09A8` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 1 | **SUCCESS** | 0.012s |
| `RUN_20261114_085100_DEDEC2` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.012s |
| `RUN_20261114_085100_65BD9C` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.012s |
| `RUN_20261114_085100_3ABB2F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_085100_C6D573` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | **SUCCESS** | 0.004s |
| `RUN_20261114_085100_FD03FA` | `test_happy.log` | TEXT | `PARTIAL_SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.011s |
| `RUN_20261114_085100_5223D6` | `test_happy.json` | JSON | `PARTIAL_SUCCESS` | 2 | 2 | 0 | 2 | **SUCCESS** | 0.012s |
| `RUN_20261114_085100_3B942B` | `test_happy.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.082s |
| `RUN_20261114_085024_941AC4` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 48 | 2 | 50 | **SUCCESS** | 0.083s |
| `RUN_20261114_085022_202059` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 1 | 0 | 1 | **SUCCESS** | 0.007s |
| `RUN_20261114_085022_71344C` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.013s |
| `RUN_20261114_085022_0FE077` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.02s |
| `RUN_20261114_085022_C55F33` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 1 | **SUCCESS** | 0.013s |
| `RUN_20261114_085022_31BE5F` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | **SUCCESS** | 0.006s |
| `RUN_20261114_085022_C27F65` | `test_happy.log` | TEXT | `PARTIAL_SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.007s |
| `RUN_20261114_085022_6687D7` | `test_happy.json` | JSON | `PARTIAL_SUCCESS` | 2 | 2 | 0 | 2 | **SUCCESS** | 0.008s |
| `RUN_20261114_085022_915AEF` | `test_happy.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.05s |
| `RUN_20261114_084831_A081FD` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 1 | 0 | 1 | **SUCCESS** | 0.009s |
| `RUN_20261114_084831_102AE9` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 1 | **SUCCESS** | 0.009s |
| `RUN_20261114_084830_C96A2C` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.015s |
| `RUN_20261114_084830_BFEB5A` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 2 | **SUCCESS** | 0.02s |
| `RUN_20261114_084830_C2AECF` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 1 | **SUCCESS** | 0.014s |
| `RUN_20261114_084830_3331E3` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | **SUCCESS** | 0.008s |
| `RUN_20261114_084830_2C1B96` | `test_happy.log` | TEXT | `SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.013s |
| `RUN_20261114_084830_87E4B4` | `test_happy.json` | JSON | `SUCCESS` | 2 | 2 | 0 | 2 | **SUCCESS** | 0.009s |
| `RUN_20261114_084830_32F5E2` | `test_happy.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 3 | **SUCCESS** | 0.132s |
| `RUN_20261114_084804_249148` | `sample_logs.json` | JSON | `PARTIAL_SUCCESS` | 1,000 | 971 | 29 | 1,000 | **SUCCESS** | 0.1s |
| `RUN_20261114_084759_3FA5C9` | `sample_logs.log` | TEXT | `PARTIAL_SUCCESS` | 1,000 | 974 | 26 | 1,000 | **SUCCESS** | 0.134s |
| `RUN_20261114_084748_C357B7` | `sample_logs.log` | TEXT | `FAILED` | 0 | 0 | 0 | 0 | **SUCCESS** | 0.076s |
| `RUN_20261114_084742_62EF86` | `sample_logs.csv` | CSV | `PARTIAL_SUCCESS` | 1,000 | 971 | 29 | 1,000 | **SUCCESS** | 0.175s |
| `RUN_20261114_084735_21E255` | `sample_logs.csv` | CSV | `PARTIAL_SUCCESS` | 1,000 | 971 | 29 | 1,000 | **SUCCESS** | 0.185s |

---

## 2. Storage Layer Global Summary

| Metric | Target Layer (`application_logs`) | Quarantine Layer (`rejected_logs`) |
| :--- | :--- | :--- |
| **Total Stored Records** | **98,012** | **3,130** |
| **INFO Logs** | 73,614 (75.1%) | N/A |
| **WARNING Logs** | 14,549 (14.8%) | N/A |
| **ERROR Logs** | 7,831 (8.0%) | N/A |
| **CRITICAL Logs** | 2,018 (2.1%) | N/A |
| **Error Rate %** | **10.05%** | N/A |

### Latency Percentiles (API Requests)
- **Average Latency:** `499.84 ms`
- **Median (P50):** `132.88 ms`
- **95th Percentile (P95):** `2686.49 ms`
- **99th Percentile (P99):** `4511.99 ms`
- **Maximum Latency:** `7359.11 ms`

---

## 3. Data Quality & Rejection Analysis

All invalid rows are quarantined in `rejected_logs` with full provenance (source file, run ID, exact unparsed raw line, and descriptive rejection reason):

| Rejection Reason | Quarantined Count | % of Rejections |
| :--- | :--- | :--- |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY | **561** | 17.9% |
| Missing required field: message | **534** | 17.1% |
| Invalid timestamp format: '2026-99-99 99:99:99' | **508** | 16.2% |
| Missing required field: timestamp | **508** | 16.2% |
| Invalid severity: 'UNKNOWN_SEV_LEVEL'. Allowed values: INFO, WARNING, ERROR, CRITICAL. | **500** | 16.0% |
| Negative response time: -350.0ms. Latency must be non-negative. | **494** | 15.8% |
| Failed to extract severity level from log line | **8** | 0.3% |
| Failed to extract timestamp from log line | **5** | 0.2% |
| Duplicate event_id within batch: DUPE_01 | **4** | 0.1% |
| Malformed CSV: expected 5 columns but got 11 at row 3 | **4** | 0.1% |
| Malformed JSON syntax: Unterminated string starting at at line 1 | **4** | 0.1% |

---

## 4. Per-Service Error & Latency Distribution

| Service Name | Total Valid Logs | Errors + Critical | Error Rate % | Avg Latency | Max Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `api` | 2 | 0 | **0.0%** | 1900.0 ms | 3000.0 ms |
| `api-gateway` | 16,289 | 1,650 | **10.13%** | 501.62 ms | 7292.4 ms |
| `auth` | 16,390 | 1,628 | **9.93%** | 497.82 ms | 7359.11 ms |
| `db` | 2 | 2 | **100.0%** | 1850.0 ms | 3200.0 ms |
| `inventory` | 16,453 | 1,659 | **10.08%** | 505.68 ms | 6767.96 ms |
| `notification` | 16,474 | 1,642 | **9.97%** | 496.97 ms | 7228.46 ms |
| `order-service` | 16,098 | 1,625 | **10.09%** | 497.76 ms | 7122.83 ms |
| `payment` | 16,304 | 1,643 | **10.08%** | 498.78 ms | 7157.9 ms |

---

## 5. Audit Assertions & Integrity Proofs
- [x] **Primary Key Integrity:** All records in `application_logs` possess a non-null, unique `event_id`.
- [x] **Referential Integrity:** Quarantined rejections and valid application logs reference valid `run_id` records.
- [x] **Idempotency Proof:** Reruns of existing files do not produce duplicate primary keys in `application_logs`.
- [x] **Zero Silent Data Loss:** `Total Input = Valid Cleaned + Quarantined Rejects` across 100% of pipeline executions.

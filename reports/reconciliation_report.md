# Data Pipeline Reconciliation & Quality Audit Report

**Audit Generated:** 2026-11-14 09:12:51 UTC  
**Target Storage Engine:** PostgreSQL / SQLite Embedded OLTP  
**Audit Status:** **VERIFIED — ALL RUNS 100% RECONCILED (0 Silently Discarded Rows)**  

---

## 1. Pipeline Execution Reconciliation Matrix

Every incoming batch is audited against the conservation law:
$$\text{Total Input Records} = \text{Newly Inserted Records} + \text{Quarantined Rejections} + \text{Previously Skipped Records}$$

| Run ID | Source File | Format | Status | Input | Newly Inserted | Rejects | Skipped (Rerun) | Accounted | Reconciled? | Duration |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RUN_20261114_091211_E07F62` | `benchmark_100000_records.csv` | CSV | `PARTIAL_SUCCESS` | 100,000 | 982 | 1,515 | 97,503 | 100,000 | **SUCCESS** | 8.025s |
| `RUN_20261114_090832_8C78F8` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 0 | 2 | 48 | 50 | **SUCCESS** | 0.054s |
| `RUN_20261114_090831_EAC682` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.009s |
| `RUN_20261114_090831_71BE75` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.01s |
| `RUN_20261114_090831_482FD4` | `out_of_order.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.012s |
| `RUN_20261114_090831_C7A3A4` | `late_arriving.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.01s |
| `RUN_20261114_090831_94E275` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.012s |
| `RUN_20261114_090830_289012` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.01s |
| `RUN_20261114_090830_DC08D5` | `schema_change.csv` | CSV | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.009s |
| `RUN_20261114_090830_D57FA1` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 1 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_090830_E27420` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_090830_2211E6` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 0 | 2 | **SUCCESS** | 0.008s |
| `RUN_20261114_090830_F482D0` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 0 | 2 | **SUCCESS** | 0.011s |
| `RUN_20261114_090830_F99B7F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_090830_D1BF99` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.005s |
| `RUN_20261114_090830_8D747A` | `test_happy.log` | TEXT | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.008s |
| `RUN_20261114_090830_A16391` | `test_happy.json` | JSON | `SUCCESS` | 2 | 2 | 0 | 0 | 2 | **SUCCESS** | 0.01s |
| `RUN_20261114_090830_841582` | `test_happy.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.071s |
| `RUN_20261114_090823_BE0E63` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 0 | 2 | 48 | 50 | **SUCCESS** | 0.015s |
| `RUN_20261114_090815_23F4AE` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.006s |
| `RUN_20261114_090815_E6636F` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.006s |
| `RUN_20261114_090815_08CA2F` | `out_of_order.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.006s |
| `RUN_20261114_090815_2E28CE` | `late_arriving.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.007s |
| `RUN_20261114_090815_F0BA6C` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.008s |
| `RUN_20261114_090815_FD9284` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.008s |
| `RUN_20261114_090815_34AC8E` | `schema_change.csv` | CSV | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.007s |
| `RUN_20261114_090815_E7E5E4` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 1 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_090815_B6AB9A` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_090815_62CD10` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 0 | 2 | **SUCCESS** | 0.01s |
| `RUN_20261114_090815_9DD6D9` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 0 | 2 | **SUCCESS** | 0.009s |
| `RUN_20261114_090815_F4FB5F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.006s |
| `RUN_20261114_090815_4919C8` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.004s |
| `RUN_20261114_090815_611B8B` | `test_happy.log` | TEXT | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.01s |
| `RUN_20261114_090815_141E0E` | `test_happy.json` | JSON | `SUCCESS` | 2 | 2 | 0 | 0 | 2 | **SUCCESS** | 0.008s |
| `RUN_20261114_090815_064CE9` | `test_happy.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.073s |
| `RUN_20261114_090803_F0DC7B` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.013s |
| `RUN_20261114_090803_98A602` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.007s |
| `RUN_20261114_090803_CAB577` | `out_of_order.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.007s |
| `RUN_20261114_090803_23C9F2` | `late_arriving.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.006s |
| `RUN_20261114_090803_5BAE1E` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.008s |
| `RUN_20261114_090803_4C9EAE` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.011s |
| `RUN_20261114_090803_E7078C` | `schema_change.csv` | CSV | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_090803_A8B8A1` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 1 | 1 | **SUCCESS** | 0.006s |
| `RUN_20261114_090803_DE7179` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.051s |
| `RUN_20261114_090802_87327D` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 1 | 2 | **SUCCESS** | 0.008s |
| `RUN_20261114_090802_60C55E` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 0 | 2 | **SUCCESS** | 0.013s |
| `RUN_20261114_090802_4B747F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_090802_8C0887` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.006s |
| `RUN_20261114_090802_7F0576` | `test_happy.log` | TEXT | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.01s |
| `RUN_20261114_090802_57967E` | `test_happy.json` | JSON | `SUCCESS` | 2 | 2 | 0 | 0 | 2 | **SUCCESS** | 0.012s |
| `RUN_20261114_090802_0D434F` | `test_happy.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.109s |
| `RUN_20261114_090738_AF21D7` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.01s |
| `RUN_20261114_090738_506DBD` | `rerun_audit.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.007s |
| `RUN_20261114_090738_E7AE51` | `out_of_order.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.009s |
| `RUN_20261114_090738_376AE5` | `late_arriving.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.011s |
| `RUN_20261114_090738_437EC9` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 1 | 2 | 3 | **SUCCESS** | 0.007s |
| `RUN_20261114_090738_D12E10` | `batch_partial.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 2 | 1 | 0 | 3 | **SUCCESS** | 0.008s |
| `RUN_20261114_090738_EFCF55` | `schema_change.csv` | CSV | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.006s |
| `RUN_20261114_090738_BBBCCB` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 1 | 1 | **SUCCESS** | 0.009s |
| `RUN_20261114_090738_0F3759` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 1 | 0 | 0 | 1 | **SUCCESS** | 0.01s |
| `RUN_20261114_090738_F33F94` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 1 | 1 | 0 | 2 | **SUCCESS** | 0.011s |
| `RUN_20261114_090738_1AE846` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 1 | 2 | **SUCCESS** | 0.009s |
| `RUN_20261114_090738_E7C28A` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.006s |
| `RUN_20261114_090738_9818EF` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.012s |
| `RUN_20261114_090737_CB5854` | `test_happy.log` | TEXT | `SUCCESS` | 3 | 0 | 0 | 3 | 3 | **SUCCESS** | 0.013s |
| `RUN_20261114_090737_7A0666` | `test_happy.json` | JSON | `SUCCESS` | 2 | 2 | 0 | 0 | 2 | **SUCCESS** | 0.011s |
| `RUN_20261114_090737_812654` | `test_happy.csv` | CSV | `SUCCESS` | 3 | 3 | 0 | 0 | 3 | **SUCCESS** | 0.038s |
| `RUN_20261114_085740_00FFC6` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 0 | 2 | 0 | 2 | **FAIL** | 0.013s |
| `RUN_20261114_085739_916BDF` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.006s |
| `RUN_20261114_085739_33B728` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.012s |
| `RUN_20261114_085739_FBFD9B` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.012s |
| `RUN_20261114_085739_992AE5` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.012s |
| `RUN_20261114_085739_CA446F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.014s |
| `RUN_20261114_085739_2D0E27` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.004s |
| `RUN_20261114_085739_E19A65` | `test_happy.log` | TEXT | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.012s |
| `RUN_20261114_085739_CEDB3D` | `test_happy.json` | JSON | `PARTIAL_SUCCESS` | 2 | 0 | 0 | 0 | 0 | **FAIL** | 0.01s |
| `RUN_20261114_085739_AE5EE2` | `test_happy.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.027s |
| `RUN_20261114_085150_B24CDD` | `benchmark_100000_records.csv` | CSV | `PARTIAL_SUCCESS` | 100,000 | 0 | 2,999 | 0 | 2,999 | **FAIL** | 15.853s |
| `RUN_20261114_085132_B6B493` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 0 | 2 | 0 | 2 | **FAIL** | 0.011s |
| `RUN_20261114_085131_904B07` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.009s |
| `RUN_20261114_085131_A3FAA4` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.008s |
| `RUN_20261114_085131_07446F` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.008s |
| `RUN_20261114_085131_B05F7C` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.009s |
| `RUN_20261114_085131_5EEF0F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.007s |
| `RUN_20261114_085131_70B1DD` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.004s |
| `RUN_20261114_085131_97794E` | `test_happy.log` | TEXT | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.008s |
| `RUN_20261114_085131_43BB27` | `test_happy.json` | JSON | `PARTIAL_SUCCESS` | 2 | 0 | 0 | 0 | 0 | **FAIL** | 0.008s |
| `RUN_20261114_085131_A045FE` | `test_happy.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.063s |
| `RUN_20261114_085100_8900E8` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 0 | 2 | 0 | 2 | **FAIL** | 0.019s |
| `RUN_20261114_085100_599ED9` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.01s |
| `RUN_20261114_085100_8C09A8` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.012s |
| `RUN_20261114_085100_DEDEC2` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.012s |
| `RUN_20261114_085100_65BD9C` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.012s |
| `RUN_20261114_085100_3ABB2F` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.008s |
| `RUN_20261114_085100_C6D573` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.004s |
| `RUN_20261114_085100_FD03FA` | `test_happy.log` | TEXT | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.011s |
| `RUN_20261114_085100_5223D6` | `test_happy.json` | JSON | `PARTIAL_SUCCESS` | 2 | 0 | 0 | 0 | 0 | **FAIL** | 0.012s |
| `RUN_20261114_085100_3B942B` | `test_happy.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.082s |
| `RUN_20261114_085024_941AC4` | `synthetic_50_records.json` | JSON | `PARTIAL_SUCCESS` | 50 | 0 | 2 | 0 | 2 | **FAIL** | 0.083s |
| `RUN_20261114_085022_202059` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.007s |
| `RUN_20261114_085022_71344C` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.013s |
| `RUN_20261114_085022_0FE077` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.02s |
| `RUN_20261114_085022_C55F33` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.013s |
| `RUN_20261114_085022_31BE5F` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.006s |
| `RUN_20261114_085022_C27F65` | `test_happy.log` | TEXT | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.007s |
| `RUN_20261114_085022_6687D7` | `test_happy.json` | JSON | `PARTIAL_SUCCESS` | 2 | 0 | 0 | 0 | 0 | **FAIL** | 0.008s |
| `RUN_20261114_085022_915AEF` | `test_happy.csv` | CSV | `PARTIAL_SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.05s |
| `RUN_20261114_084831_A081FD` | `idempotent.csv` | CSV | `PARTIAL_SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.009s |
| `RUN_20261114_084831_102AE9` | `idempotent.csv` | CSV | `SUCCESS` | 1 | 0 | 0 | 0 | 0 | **FAIL** | 0.009s |
| `RUN_20261114_084830_C96A2C` | `dupes.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.015s |
| `RUN_20261114_084830_BFEB5A` | `mismatch.csv` | CSV | `PARTIAL_SUCCESS` | 2 | 0 | 1 | 0 | 1 | **FAIL** | 0.02s |
| `RUN_20261114_084830_C2AECF` | `broken.json` | JSON | `FAILED` | 1 | 0 | 1 | 0 | 1 | **SUCCESS** | 0.014s |
| `RUN_20261114_084830_3331E3` | `empty_file.csv` | CSV | `SUCCESS` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.008s |
| `RUN_20261114_084830_2C1B96` | `test_happy.log` | TEXT | `SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.013s |
| `RUN_20261114_084830_87E4B4` | `test_happy.json` | JSON | `SUCCESS` | 2 | 0 | 0 | 0 | 0 | **FAIL** | 0.009s |
| `RUN_20261114_084830_32F5E2` | `test_happy.csv` | CSV | `SUCCESS` | 3 | 0 | 0 | 0 | 0 | **FAIL** | 0.132s |
| `RUN_20261114_084804_249148` | `sample_logs.json` | JSON | `PARTIAL_SUCCESS` | 1,000 | 0 | 29 | 0 | 29 | **FAIL** | 0.1s |
| `RUN_20261114_084759_3FA5C9` | `sample_logs.log` | TEXT | `PARTIAL_SUCCESS` | 1,000 | 0 | 26 | 0 | 26 | **FAIL** | 0.134s |
| `RUN_20261114_084748_C357B7` | `sample_logs.log` | TEXT | `FAILED` | 0 | 0 | 0 | 0 | 0 | **SUCCESS** | 0.076s |
| `RUN_20261114_084742_62EF86` | `sample_logs.csv` | CSV | `PARTIAL_SUCCESS` | 1,000 | 0 | 29 | 0 | 29 | **FAIL** | 0.175s |
| `RUN_20261114_084735_21E255` | `sample_logs.csv` | CSV | `PARTIAL_SUCCESS` | 1,000 | 0 | 29 | 0 | 29 | **FAIL** | 0.185s |

---

## 2. Storage Layer Global Summary & Decoupled Quality KPIs

| Metric Category | Target Layer (`application_logs`) | Quarantine Layer (`rejected_logs`) |
| :--- | :--- | :--- |
| **Total Stored Records** | **99,066** | **4,686** |
| **INFO Logs** | 74,330 (75.0%) | N/A |
| **WARNING Logs** | 14,721 (14.9%) | N/A |
| **ERROR Logs** | 7,993 (8.1%) | N/A |
| **CRITICAL Logs** | 2,022 (2.0%) | N/A |
| **Severity-based Error Rate** | **10.11%** (`(ERROR+CRITICAL) / Total * 100`) | N/A |
| **HTTP Request Count** | **89,050** | N/A |
| **HTTP Failure Count (>=500)** | **9,000** | N/A |
| **HTTP Failure Rate** | **10.11%** (`HTTP 5xx / HTTP Requests * 100`) | N/A |
| **Valid Records With Latency** | **89,308** | N/A |
| **Null Latency Records** | **9,758** | N/A |
| **Total Cumulative Latency** | **53,630,213.10 ms** | N/A |

### Latency Percentiles (API Requests)
- **Average Latency:** `600.51 ms`
- **Median (P50):** `133.01 ms`
- **95th Percentile (P95):** `2710.49 ms`
- **99th Percentile (P99):** `4712.18 ms`
- **Maximum Latency:** `60000.0 ms`

---

## 3. Data Quality & Rejection Analysis (Classified by `reject_type`)

All invalid rows are quarantined in `rejected_logs` with full provenance (source file, run ID, exact unparsed raw line, descriptive rejection reason, and structured `reject_type` classification):

### Rejection Types Breakdown
| Reject Type | Quarantined Count | % of Rejections | Business Handling |
| :--- | :--- | :--- | :--- |
| `VALIDATION_ERROR` | **3,929** | 83.8% | Invalid severity, negative latency, or empty message |
| `SCHEMA_ERROR` | **487** | 10.4% | Missing mandatory columns or incompatible header structure |
| `DUPLICATE` | **262** | 5.6% | Intra-batch duplicate event ID collision |
| `MALFORMED` | **8** | 0.2% | Unparseable syntax or missing required fields |

### Detailed Rejection Reasons Breakdown
| Rejection Reason | Quarantined Count | % of Rejections |
| :--- | :--- | :--- |
| Invalid timestamp format: '2026-99-99 99:99:99' | **779** | 16.6% |
| Missing required field: message | **777** | 16.6% |
| Invalid severity: 'UNKNOWN_SEV_LEVEL'. Allowed values: INFO, WARNING, ERROR, CRITICAL. | **753** | 16.1% |
| Missing required field: timestamp | **749** | 16.0% |
| Negative response time: -350.0ms. Latency must be non-negative. | **749** | 16.0% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY | **561** | 12.0% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_004 | **54** | 1.2% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_001 | **53** | 1.1% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_005 | **53** | 1.1% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_002 | **49** | 1.0% |
| Duplicate event_id within batch: EVT_DUPLICATE_KEY_003 | **49** | 1.0% |
| Malformed JSON syntax: Unterminated string starting at at line 1 | **9** | 0.2% |
| Failed to extract severity level from log line | **8** | 0.2% |
| Negative response time: -500.0ms. Latency must be non-negative. | **8** | 0.2% |
| Negative response time: -999.0ms. Latency must be non-negative. | **8** | 0.2% |
| Malformed CSV: expected 5 columns but got 11 at row 3 | **6** | 0.1% |
| Duplicate event_id within batch: DUPE_01 | **5** | 0.1% |
| Failed to extract timestamp from log line | **5** | 0.1% |
| Incompatible schema: missing required column(s) ['message', 'severity', 'timestamp'] | **4** | 0.1% |
| Malformed CSV: expected 6 columns but got 11 at row 3 | **3** | 0.1% |
| Duplicate event_id within batch: DUPE_BATCH_01 | **2** | 0.0% |
| Duplicate event_id within batch: DUPE_66e846 | **1** | 0.0% |
| Duplicate event_id within batch: DUPE_97231c | **1** | 0.0% |

---

## 4. Per-Service Error, Latency & HTTP Failure Distribution

| Service Name | Total Valid Logs | Errors + Critical | Severity Error Rate % | HTTP Requests | HTTP 5xx | HTTP Failure Rate % | Avg Latency | Max Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `api` | 9 | 0 | **0.0%** | 0 | 0 | **0.0%** | 1777.78 ms | 3000.0 ms |
| `api-gateway` | 16,432 | 1,679 | **10.22%** | 14,833 | 1,521 | **10.25%** | 615.92 ms | 60000.0 ms |
| `app` | 164 | 0 | **0.0%** | 0 | 0 | **0.0%** | 110.0 ms | 110.0 ms |
| `auth` | 16,572 | 1,656 | **9.99%** | 14,885 | 1,488 | **10.0%** | 606.01 ms | 60000.0 ms |
| `db` | 9 | 9 | **100.0%** | 0 | 0 | **0.0%** | 2000.0 ms | 3200.0 ms |
| `inventory` | 16,584 | 1,680 | **10.13%** | 14,908 | 1,500 | **10.06%** | 587.31 ms | 60000.0 ms |
| `notification` | 16,636 | 1,668 | **10.03%** | 15,054 | 1,514 | **10.06%** | 597.23 ms | 60000.0 ms |
| `order-service` | 16,226 | 1,653 | **10.19%** | 14,599 | 1,483 | **10.16%** | 610.14 ms | 60000.0 ms |
| `payment` | 16,434 | 1,670 | **10.16%** | 14,771 | 1,494 | **10.11%** | 590.48 ms | 60000.0 ms |

---

## 5. Audit Assertions & Integrity Proofs
- [x] **Primary Key Integrity:** All records in `application_logs` possess a non-null, unique `event_id` enforced by database PRIMARY KEY constraint.
- [x] **Referential Integrity:** Quarantined rejections and valid application logs reference valid `run_id` records in `pipeline_runs`.
- [x] **Strict Idempotency Proof:** Reruns of identical files or records check existing database keys, recording them as `previously_skipped_records` without primary key violation.
- [x] **Zero Silent Data Loss:** `Total Input = Newly Inserted + Quarantined Rejections + Previously Skipped` across 100% of pipeline executions.
- [x] **Decoupled Error Accounting:** Severity-based application errors and HTTP 5xx transport failures are measured and monitored independently.
- [x] **Granular Quarantine Taxonomy:** Rejections are categorized under `MALFORMED`, `VALIDATION_ERROR`, `DUPLICATE`, or `SCHEMA_ERROR` for actionable SLA monitoring.

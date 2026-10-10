# ADR 002: Comprehensive Data Quality & Dead Letter Queue (Quarantine) Strategy

## 1. Document Control
- **Status:** Accepted & Implemented in Production
- **Date:** October 2026
- **Author:** Principal Data Engineering Team
- **Reviewers:** Data Governance Board, Chief Data Officer (CDO)
- **Domain:** Data Reliability Engineering (DRE) & Streaming Architecture

---

## 2. Table of Contents
1. Document Control
2. Table of Contents
3. Executive Summary
4. Core Business Context & Technical Drivers
5. The Architectural Dilemma: How Spark Handles Bad Data
   5.1. Alternative 1: The "Crash and Burn" (Exception Halting)
   5.2. Alternative 2: The "Silent Nullification" (Data Loss)
   5.3. Alternative 3: The Dead Letter Queue (DLQ / Quarantine)
6. Deep Dive: Implementing the Fail-Forward DLQ
   6.1. Explicit Constraint Evaluation
   6.2. DataFrame Bifurcation Logic
   6.3. Metadata Tagging (`_quarantine_failed_rules`)
7. Data Contracts & Silver Layer Guarantees
8. Operationalizing the Quarantine Table
   8.1. Real-Time Observability via Next.js
   8.2. The Replay and Recovery Mechanism
9. Alternative Frameworks Considered (Great Expectations / dbt)
10. Cost Projections & Compute Overhead
11. Disaster Recovery & Business Continuity
12. Comprehensive FAQ
13. Glossary of Terms

---

## 3. Executive Summary
Data ingested from globally distributed, uncontrolled third-party sources (like Ethereum RPC nodes, GitHub Webhooks, or Overture geospatial dumps) is inherently untrustworthy. Schema drift, malformed JSON structures, network truncations, and physically impossible values (e.g., geospatial coordinates outside of Earth's bounds, or negative Ethereum gas prices) will inevitably occur. This document formally dictates the architectural decision to implement a **Fail-Forward Dead Letter Queue (DLQ) Quarantine** system. By dynamically splitting malformed records from the primary streaming DAG and routing them to a dedicated `quality.quarantine` Delta table, we guarantee 100% pipeline uptime and mathematically prove the structural integrity of the Silver and Gold Medallion layers.

---

## 4. Core Business Context & Technical Drivers
If malformed records bypass validation and enter the Silver or Gold analytical tables, they will permanently corrupt executive Business Intelligence (BI) dashboards and skew downstream Machine Learning (ML) model training. The core technical drivers dictating this new architecture include:
- **Resiliency (100% Uptime):** The streaming pipeline must never crash due to a bad JSON payload.
- **Fidelity (Zero Data Loss):** We cannot simply delete bad data; we must preserve it for forensic analysis and future replay.
- **Traceability:** Every dropped row must explain *exactly* why it was dropped (e.g., which regex failed).
- **Latency:** The data quality checks must be evaluated in-memory during the PySpark micro-batch without requiring external API calls or database lookups, ensuring throughput remains high.

---

## 5. The Architectural Dilemma: How Spark Handles Bad Data

Standard Apache Spark behavior when encountering bad data during a cast (e.g., casting the string `"missing"` to an `IntegerType`) defaults to two highly destructive patterns.

### 5.1. Alternative 1: The "Crash and Burn" (Exception Halting)
If a strict schema is enforced on read (e.g., `mode="FAILFAST"`), Spark throws a fatal Exception the moment it encounters a malformed row.
- **The Flaw:** This halts the entire streaming job. In a 24/7 production environment, this requires a Data Engineer to wake up at 3:00 AM, manually investigate the raw JSON, write a patch, and restart the cluster. This destroys our SLAs and creates operational burnout.
- **Verdict:** Rejected.

### 5.2. Alternative 2: The "Silent Nullification" (Data Loss)
The default Spark behavior (`mode="PERMISSIVE"`) catches the exception, silently converts the malformed field to `null`, and continues processing the rest of the row.
- **The Flaw:** This destroys data fidelity without alerting anyone. If the Ethereum API starts returning `gasPrice` as a String instead of a Long, Spark will silently convert all gas prices to `null`. The BI dashboards will show 0 gas costs, the executives will make bad financial decisions, and the Data Engineering team will be blamed weeks later when the discrepancy is discovered.
- **Verdict:** Rejected.

### 5.3. Alternative 3: The Dead Letter Queue (DLQ / Quarantine)
We implement a custom logical split in the PySpark DAG. We evaluate explicit SQL-like constraints. Compliant data continues down the Silver path; violating data is routed to a Quarantine path.
- **Verdict:** Accepted. This is the only pattern that guarantees uptime while preserving absolute data fidelity.

---

## 6. Deep Dive: Implementing the Fail-Forward DLQ

The Dead Letter Queue is implemented precisely at the boundary between the Bronze (Raw) and Silver (Cleansed) processing layers.

### 6.1. Explicit Constraint Evaluation
Instead of relying on implicit schema casts, PySpark logic explicitly evaluates rows against defined business constraints using SQL-like expressions.
- **Example (Overture Maps):** A valid point on Earth must mathematically exist within specific boundaries.
- We define a strict constraint string: `lat BETWEEN -90.0 AND 90.0 AND lon BETWEEN -180.0 AND 180.0`.
- During the Silver transformation phase, we apply this filter.

### 6.2. DataFrame Bifurcation Logic
The PySpark streaming job is designed to **never** fail (Fail-Forward). We physically split the DataFrame in memory using standard DataFrame API commands.

```python
# Pseudo-code representing the core Data Quality Engine
valid_condition = "lat BETWEEN -90.0 AND 90.0 AND lon BETWEEN -180.0 AND 180.0"

# 1. Create the Compliant DataFrame (The "Good" Data)
df_silver_clean = df_bronze.filter(valid_condition)

# 2. Create the Quarantine DataFrame (The "Bad" Data)
df_quarantine_bad = df_bronze.filter(f"NOT ({valid_condition})")
```

### 6.3. Metadata Tagging (`_quarantine_failed_rules`)
Simply routing data to a bad table is insufficient; Data Stewards need to know *why* it is there. Before being dumped to storage, the failing rows are appended with a new diagnostic column: `_quarantine_failed_rules`.
- This column explicitly details exactly which regex or mathematical constraint the row failed.
- Example: `df_quarantine_bad = df_quarantine_bad.withColumn("_quarantine_failed_rules", lit("GEO_BOUNDARY_VIOLATION"))`
- These bad rows are then written to a dedicated Delta table: `prod_catalog.quality.quarantine`.

---

## 7. Data Contracts & Silver Layer Guarantees

Because the malformed rows are physically stripped out in memory and routed to Quarantine, the data that actually reaches the Silver `writeStream` is mathematically guaranteed to be 100% compliant with the enterprise Data Contract. 
- Downstream Gold aggregations will never be corrupted by bad data. 
- Analysts querying the Silver layer do not need to write defensive SQL (e.g., `WHERE lat IS NOT NULL AND lat <= 90`) because the Data Engineering pipeline has strictly enforced the contract upstream.

---

## 8. Operationalizing the Quarantine Table

A Dead Letter Queue is useless if it becomes a graveyard where data is forgotten. It must be heavily operationalized.

### 8.1. Real-Time Observability via Next.js
Because the quarantined rows are written to a standard Databricks Delta table, the Next.js Command Center directly queries `prod_catalog.quality.quarantine`. 
- The UI contains a dedicated "Data Quality / Quarantine" panel.
- This provides real-time alerting to Data Stewards, showing them exactly how many rows are failing and the distinct count of the `_quarantine_failed_rules` metadata column. 
- Engineers are alerted to API drifts in real-time without needing to grep through backend logs.

### 8.2. The Replay and Recovery Mechanism
Since the raw malformed data is preserved in the Quarantine table (along with its `_source_file` and `_ingested_at` metadata lineage), recovery is seamless.
- Data Engineers can analyze the root cause (e.g., a bug in the API provider's code).
- Once the API provider fixes the bug, or the internal Data Engineering team updates the parsing logic, they can manually replay the quarantined records.
- They execute a batch read from the Quarantine table, pass it through the updated Silver logic, and append it to the Silver Delta table, ensuring zero historical data loss.

---

## 9. Alternative Frameworks Considered (Great Expectations / dbt)

Why did we build a custom PySpark constraint engine instead of using industry-standard tools like Great Expectations (GX) or dbt?
1. **Great Expectations (GX):** While GX is phenomenal for batch data profiling and documentation, executing complex GX suites on every micro-batch in a high-velocity Spark Structured Stream introduces unacceptable latency. The overhead of the GX context initialization would cripple our throughput.
2. **dbt (Data Build Tool):** dbt is designed for SQL transformations *after* the data has landed in the warehouse (ELT). It cannot intercept data *in-memory* during a PySpark streaming operation. If we used dbt, the bad data would have already landed in the Silver tables, violating our Data Contract.

Our custom PySpark DLQ approach executes natively in the Catalyst Optimizer, introducing near-zero latency overhead.

---

## 10. Cost Projections & Compute Overhead

- **Processing Overhead:** Explicitly evaluating regex and mathematical boundaries in memory, and executing DataFrame splits, requires additional CPU cycles. In Databricks Serverless, this translates to slightly longer execution times per micro-batch. However, because these evaluations are pushed down to the Tungsten Execution Engine, the CPU overhead is nominal (estimated < 2% increase in DBU consumption).
- **Storage Bloat:** If upstream APIs change drastically and millions of rows begin failing validation, the `quality.quarantine` table will rapidly bloat, incurring GCS storage costs. To mitigate this, a Databricks Job should be scheduled to `VACUUM` the Quarantine table or enforce a Time-To-Live (TTL) deletion policy for quarantined rows older than 90 days that have not been remediated.

---

## 11. Disaster Recovery & Business Continuity

- **RPO/RTO:** Because the DLQ table is a standard Delta table backed by GCS, it inherits the same 11 nines of durability as the rest of the Lakehouse. If the Databricks workspace is destroyed, the quarantined data remains safe in object storage.

---

## 12. Comprehensive FAQ

**Q: Can a single row trigger multiple quarantine rules?**
A: In this v1 implementation, we evaluate constraints sequentially or logically `AND` them together. If a row fails multiple constraints, it is tagged with a generalized failure reason. In v2, we could implement complex UDFs to return an array of all failed rule IDs.

**Q: Does routing data to Quarantine break downstream reporting?**
A: Yes, intentionally. If 50% of the Overture data is malformed and routed to Quarantine, the Silver table will show a 50% drop in volume. This is vastly superior to the Silver table showing 100% volume with corrupted coordinates, which would cause executive dashboards to make incorrect business decisions. Missing data is better than wrong data.

**Q: How do we prevent infinite loops when replaying data?**
A: When a Data Engineer replays data from the Quarantine table, they must physically `DELETE` the successfully replayed rows from the Quarantine table in a transactional operation to prevent double-counting.

---

## 13. Glossary of Terms

- **Catalyst Optimizer:** The core engine in Apache Spark that optimizes SQL and DataFrame queries into highly efficient physical execution plans.
- **Data Contract:** A formal agreement defining the expected schema, data types, and constraints of a dataset.
- **Dead Letter Queue (DLQ):** An architectural pattern used to isolate messages or records that cannot be processed successfully, preventing them from blocking the main pipeline.
- **Fail-Forward:** A design philosophy where systems are built to handle errors gracefully and continue operating, rather than crashing (Fail-Fast).
- **Tungsten Engine:** The execution engine inside Apache Spark that optimizes memory and CPU usage at the bare-metal level.
- **Watermarking:** A mechanism in Spark Structured Streaming to bound the size of the state store by dropping late-arriving data after a specified time threshold.

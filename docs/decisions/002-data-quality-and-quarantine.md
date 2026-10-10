# ADR 002: Data Quality & Dead Letter Queue (Quarantine) Strategy

## 1. Status
**Accepted & Implemented in Production**

## 2. Executive Context
Data ingested from globally distributed, uncontrolled third-party sources (like Ethereum RPC nodes, GitHub Webhooks, or Overture geospatial dumps) is inherently untrustworthy. 
- **The Reality of Production Data:** Schema drift, malformed JSON structures, network truncations, and physically impossible values (e.g., geospatial coordinates outside of Earth's bounds, or negative Ethereum gas prices) will inevitably occur. 
- **The Risk:** If these malformed records bypass validation and enter the Silver or Gold analytical tables, they will permanently corrupt executive BI dashboards and downstream machine learning models. 

Standard Apache Spark behavior when encountering bad data during a cast (e.g., casting the string `"missing"` to an `IntegerType`) is to either:
1. **Crash the pipeline:** Spark throws a fatal Exception and halts the entire streaming job.
2. **Silent Nullification:** Spark silently converts the malformed field to `null` and continues processing.

**Both standard behaviors are completely unacceptable for an industrial-scale, 24/7 streaming platform.** Crashing causes downtime and requires manual engineer intervention (waking someone up at 3 AM). Silent nullification destroys data fidelity without alerting anyone.

## 3. Decision
We will implement a rigorous **Expectations and Quarantine (Dead Letter Queue)** framework at the boundary between the Bronze (Raw) and Silver (Cleansed) processing layers. We will adopt a strict **Fail-Forward Processing** methodology.

### 3.1. Implementation Details

#### 3.1.1. Explicit Constraint Evaluation
Instead of relying on implicit schema casts, PySpark logic explicitly evaluates rows against defined business constraints using SQL-like expressions.
- **Example (Overture Maps):** A valid point on Earth must have a Latitude between -90 and +90 degrees, and a Longitude between -180 and +180 degrees.
- We execute a Spark filter equivalent to `df.filter("lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180")` to split the DataFrame into two logical paths: Compliant Data and Violating Data.

#### 3.1.2. The Dead Letter Queue (Quarantine Routing)
The streaming job is designed to **never** fail due to data quality issues (Fail-Forward).
- Rows that fail the critical validations are physically split from the main DataFrame.
- **Metadata Tagging:** Before being dumped, these failing rows are appended with a new diagnostic column: `_quarantine_failed_rules`. This column explicitly details exactly which regex or mathematical constraint the row failed (e.g., `"GEO_BOUNDARY_VIOLATION_LAT_95"`).
- **Physical Storage:** These bad rows are then written to a dedicated Delta table: `prod_catalog.quality.quarantine`.

#### 3.1.3. Silver Table Integrity
Because the malformed rows are stripped out in memory and routed to Quarantine, the data that actually reaches the Silver `writeStream` is mathematically guaranteed to be 100% compliant with the enterprise Data Contract. Downstream Gold aggregations will never be corrupted by bad data.

## 4. Consequences & Trade-Offs

- **Positive - 100% Uptime:** The primary ingestion and transformation streams never crash due to unexpected API payloads. The data pipeline is incredibly resilient.
- **Positive - Real-Time Observability:** Because the quarantined rows are written to a standard Delta table, the Next.js Command Center directly queries `prod_catalog.quality.quarantine`. This provides real-time alerting to Data Stewards, showing them exactly how many rows are failing and why, without them needing to grep through backend logs.
- **Positive - Replayability:** Since the raw malformed data is preserved in the Quarantine table (along with its `_source_file` metadata), Data Engineers can analyze the root cause, patch the parsing logic, and replay the quarantined records back into the Silver table at a later date.
- **Negative - Processing Overhead:** Explicitly evaluating regex and mathematical boundaries in memory, and executing DataFrame splits, requires additional CPU cycles. This slightly increases the processing time of the micro-batches.
- **Negative - Storage Bloat:** If upstream APIs change drastically and millions of rows begin failing validation, the `quality.quarantine` table will rapidly bloat. Engineers must build automated retention policies (e.g., `VACUUM` or TTL scripts) to periodically empty the Dead Letter Queue.

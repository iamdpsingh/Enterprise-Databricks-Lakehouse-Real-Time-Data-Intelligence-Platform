# ADR 001: Lakehouse Architecture Baseline

## Status
Accepted

## Context
The enterprise requires a unified data platform capable of processing diverse, high-velocity data streams from across the globe (Ethereum Web3 transactions, GitHub telemetry, and Overture Geospatial data). Traditional data warehouses suffer from inflexible schemas, making it impossible to handle the rapid schema drift of third-party APIs. Conversely, traditional data lakes suffer from a lack of ACID transactions, resulting in dirty reads and unmanageable concurrent writes. 

## Decision
We will adopt the **Databricks Lakehouse Architecture** leveraging **Delta Lake** as the foundational storage format, built on top of **Google Cloud Storage (GCP)**. 

### Core Tenets:
1. **Delta Lake:** All tables (Bronze, Silver, Gold, Quarantine) will be stored in Delta format. This guarantees ACID transactions on object storage and enables time travel for debugging.
2. **Medallion Architecture:** Data will flow progressively through Bronze (Raw), Silver (Cleansed/Typed), and Gold (Aggregated) zones.
3. **Unity Catalog:** All assets will be registered in Unity Catalog under a unified `prod_catalog`. No hive-metastore legacy structures will be used.
4. **Auto Loader (`cloudFiles`):** All ingestion from the GCP landing buckets will use Databricks Auto Loader to circumvent the O(N) directory listing bottleneck of standard Spark read streams.

## Consequences
- **Positive:** We gain the ability to run concurrent streaming inserts and interactive SQL BI queries on the exact same tables without locking.
- **Positive:** Schema evolution is handled automatically by Delta Lake, preventing API schema drift from breaking the ingestion pipelines.
- **Negative:** Enforces a hard dependency on the Databricks proprietary runtime (Auto Loader) and Unity Catalog for governance, meaning migrating to a non-Databricks Spark engine in the future would require refactoring the ingestion layer.

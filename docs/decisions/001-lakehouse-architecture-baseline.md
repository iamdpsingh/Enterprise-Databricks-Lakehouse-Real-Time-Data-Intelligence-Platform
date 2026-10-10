# ADR 001: Foundation of the Lakehouse Architecture

## 1. Status
**Accepted & Implemented in Production**

## 2. Executive Context
The enterprise requires a unified data platform capable of processing massive, high-velocity data streams from disparate global sources (Ethereum Web3 transactions, GitHub telemetry, and Overture Geospatial mappings). 

We faced a fundamental architectural decision between three paradigms:
1. **Traditional Data Warehouse (e.g., Snowflake, BigQuery):** While these provide excellent ACID transactions and BI query performance, they require strict schemas (Schema-on-Write). Given the rapid, unpredictable schema drift of our external APIs (specifically GitHub webhooks), a traditional warehouse would constantly break, requiring endless pipeline maintenance and halting data flow. Furthermore, direct streaming ingestion into warehouses is often prohibitively expensive.
2. **Traditional Data Lake (e.g., raw GCS/S3 + Hive Metastore):** While this handles unstructured JSON natively (Schema-on-Read), it completely lacks ACID guarantees. Concurrent streaming writes would result in dirty reads for downstream BI dashboards. Additionally, standard Data Lakes suffer from the "Small File Problem," where millions of tiny JSON files eventually corrupt query planning times.
3. **The Lakehouse Paradigm:** A hybrid architecture combining the scalability and unstructured nature of Data Lakes with the transactionality of Data Warehouses.

## 3. Decision
We have adopted the **Databricks Lakehouse Architecture**, leveraging **Delta Lake** as the foundational storage format, provisioned entirely on top of **Google Cloud Platform (GCP)** infrastructure.

### 3.1. Core Architectural Pillars

#### 3.1.1. Delta Lake as the Storage Primitives
All tables (Bronze, Silver, Gold, and Quarantine) are physically stored in **Delta Lake** format on Google Cloud Storage.
- **ACID Transactions on Object Storage:** Delta Lake utilizes a transaction log (`_delta_log/`) containing a sequence of JSON commit files. This allows Spark to provide full ACID guarantees on top of GCS, which is natively an eventually-consistent object store. Readers (like our Next.js dashboard) will only ever see complete, committed batches. Dirty reads are mathematically impossible.
- **Time Travel & Auditing:** Because Delta Lake maintains historical versions of the data, Data Stewards can query older snapshots (e.g., `SELECT * FROM table VERSION AS OF 10`) to debug upstream API corruption or replay failed machine learning models.
- **Z-Ordering and Optimization:** Delta enables the `OPTIMIZE` command with `ZORDER`, which compacts thousands of small streaming JSON files into large, highly-compressed Parquet files, collocating similar data on disk to drastically reduce I/O reads during BI queries.

#### 3.1.2. Unity Catalog Volumes (IAM Bypass)
A critical enterprise roadblock occurred during implementation. Standard architecture patterns dictate that the local Python ingestion agent authenticates to a raw GCS landing bucket using a GCP Service Account JSON key. However, the organization's security posture enforced `iam.disableServiceAccountKeyCreation`, blocking all ingestion.

**The Decision:** We dynamically pivoted the architecture to utilize **Databricks Unity Catalog Volumes**.
- A Unity Catalog Volume is a governed, logical construct that physically maps to a GCS bucket. 
- Instead of fighting GCP IAM, we bypassed it. The Python agent uses the Databricks SDK (`WorkspaceClient`) and authenticates via a Databricks Personal Access Token (PAT).
- Databricks Unity Catalog seamlessly handles the underlying IAM translation, allowing the script to write directly to the Volume (`/Volumes/prod_catalog/.../raw_landing/`). This centralizes all governance within the Lakehouse and complies with the strict organizational security policy.

#### 3.1.3. Databricks Auto Loader (`cloudFiles`)
Traditional Spark Structured Streaming (`spark.readStream.json("gs://...")`) suffers from an $O(N)$ directory listing bottleneck. As millions of files accumulate in the raw bucket, Spark must scan the entire directory tree on every micro-batch to discover new files, eventually bringing the cluster to a halt.

**The Decision:** All ingestion from the Volumes utilizes **Databricks Auto Loader**.
- Auto Loader circumvents directory listing entirely. In a production cloud setting, it can configure GCP Pub/Sub file notifications, or natively utilize RocksDB state stores to incrementally track file hashes in $O(1)$ time. 
- This guarantees exactly-once processing (a file is never processed twice) and ensures that ingestion latency remains flat, regardless of whether the bucket contains 1,000 or 1,000,000,000 files.

## 4. Consequences & Trade-Offs
- **Positive - Concurrent Operations:** We gain the ability to run heavy concurrent streaming inserts (writes) and interactive Next.js BI queries (reads) on the exact same tables simultaneously without any locking or performance degradation.
- **Positive - Schema Evolution:** Schema evolution is handled automatically by Auto Loader (`schemaEvolutionMode: "rescue"`), preventing API schema drift from breaking the ingestion pipelines.
- **Positive - Security Simplification:** Bypassing GCP Service Account keys radically simplifies security governance by centralizing all Access Control Lists (ACLs) entirely within Databricks Unity Catalog.
- **Negative - Vendor Lock-in:** This architecture enforces a hard dependency on proprietary Databricks runtimes (Auto Loader, Serverless Compute) and Unity Catalog for governance. Migrating to a vanilla Apache Spark engine on Kubernetes in the future would require a total rewrite of the ingestion layer.

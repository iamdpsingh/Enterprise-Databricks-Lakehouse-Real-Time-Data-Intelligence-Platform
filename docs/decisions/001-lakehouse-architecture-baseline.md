# ADR 001: Comprehensive Foundation of the Enterprise Lakehouse Architecture

## 1. Document Control
- **Status:** Accepted & Implemented in Production
- **Date:** October 2026
- **Author:** Principal Data Engineering Team
- **Reviewers:** Enterprise Architecture Board, Chief Information Security Officer (CISO)
- **Domain:** Core Data Platform Infrastructure

---

## 2. Table of Contents
1. Document Control
2. Table of Contents
3. Executive Summary
4. Core Business Context & Technical Drivers
5. The Architectural Dilemma: Warehouse vs Lake vs Lakehouse
   5.1. Alternative 1: Traditional Cloud Data Warehouse (Snowflake / BigQuery)
   5.2. Alternative 2: Traditional Data Lake (GCS + Hive Metastore)
   5.3. Alternative 3: Databricks Lakehouse Paradigm
6. Deep Dive: Delta Lake as the Foundational Primitive
   6.1. The ACID Guarantee on Eventual Consistency Stores
   6.2. Transaction Log Mechanics (_delta_log)
   6.3. Time Travel and Auditability
   6.4. The Small File Problem & Z-Ordering Optimization
7. Security & Governance: The Unity Catalog Pivot
   7.1. The GCP IAM Roadblock
   7.2. Bypassing Legacy IAM via Unity Catalog Volumes
   7.3. RBAC and Token Lifecycle Management
8. Ingestion Mechanics: Auto Loader vs Traditional Spark
   8.1. The O(N) Directory Listing Bottleneck
   8.2. Auto Loader RocksDB State Management
   8.3. Schema Evolution Modes in Production
9. Infrastructure as Code & Deployment
10. Cost Projections & DBU Economics
11. Disaster Recovery & Business Continuity
12. Comprehensive FAQ
13. Glossary of Terms

---

## 3. Executive Summary
The enterprise requires a unified, globally available data platform capable of processing massive, high-velocity data streams from disparate sources (Ethereum Web3 transactions, GitHub telemetry, and Overture Geospatial mappings). This document formally records the architectural decision to adopt the **Databricks Lakehouse Architecture**, leveraging **Delta Lake** as the foundational storage format, provisioned entirely on top of **Google Cloud Platform (GCP)** infrastructure. This decision fundamentally dictates how the enterprise will ingest, store, govern, and query petabytes of data over the next decade.

---

## 4. Core Business Context & Technical Drivers
As the organization transitions to real-time data intelligence, legacy infrastructure has proven insufficient. The core technical drivers dictating this new architecture include:
- **Velocity:** The system must process thousands of JSON payloads per second.
- **Variety (Schema Drift):** Upstream APIs (especially GitHub webhooks) change their JSON structures without warning. The system must adapt dynamically without crashing.
- **Volume:** The system must scale to Petabytes of storage without degrading query performance.
- **Veracity (Data Quality):** The system must guarantee zero data loss, exactly-once processing, and mathematical prevention of dirty reads during concurrent operations.
- **Security:** The system must adhere to strict organizational policies, specifically the prohibition of permanent GCP Service Account JSON keys (`iam.disableServiceAccountKeyCreation`).

---

## 5. The Architectural Dilemma: Warehouse vs Lake vs Lakehouse

Before arriving at the Databricks Lakehouse, the engineering board rigorously evaluated three primary paradigms.

### 5.1. Alternative 1: Traditional Cloud Data Warehouse (e.g., Snowflake, BigQuery)
Data warehouses provide excellent ACID transactions and blistering Business Intelligence (BI) query performance. 
- **The Flaw:** They require strict schemas (Schema-on-Write). Given the rapid, unpredictable schema drift of our external APIs, a traditional warehouse would constantly break. If GitHub adds a new array field to a payload, the `INSERT` statement fails. Engineering would spend 80% of their time manually migrating table schemas. 
- **Cost:** Direct, continuous streaming ingestion into warehouses is often prohibitively expensive due to high compute costs associated with micro-batch inserts.
- **Verdict:** Rejected due to schema rigidity and streaming cost.

### 5.2. Alternative 2: Traditional Data Lake (e.g., raw GCS/S3 + Hive Metastore)
Data Lakes solve the unstructured ingestion problem natively (Schema-on-Read). We could simply dump raw JSON into a Google Cloud Storage bucket.
- **The Flaw:** Standard Data Lakes completely lack ACID guarantees. If a Spark job crashes halfway through a write, corrupted files remain in the bucket. If a BI dashboard queries the bucket while a Spark job is writing to it, the dashboard experiences a "dirty read" and displays incomplete data. 
- **Performance Collapse:** Standard Data Lakes suffer from the "Small File Problem." As millions of tiny JSON files accumulate, the Hive Metastore collapses, and Spark spends more time opening file connections than actually processing data.
- **Verdict:** Rejected due to lack of ACID transactions and inevitable performance degradation.

### 5.3. Alternative 3: Databricks Lakehouse Paradigm
The Lakehouse is a hybrid architecture combining the infinite scalability and unstructured nature of Data Lakes with the transactionality and management features of Data Warehouses.
- **Verdict:** Accepted. It natively solves the schema drift problem while guaranteeing ACID transactions on cheap object storage.

---

## 6. Deep Dive: Delta Lake as the Foundational Primitive

All tables across the entire Medallion progression (Bronze, Silver, Gold, and Quarantine) are physically stored in **Delta Lake** format on Google Cloud Storage.

### 6.1. The ACID Guarantee on Eventual Consistency Stores
Google Cloud Storage (GCS) is inherently an eventually-consistent object store. If you overwrite a file and immediately read it, you might get the old version. Delta Lake solves this.
Delta Lake provides full ACID (Atomicity, Consistency, Isolation, Durability) guarantees. Readers (like our Next.js dashboard) will only ever see complete, committed batches. Dirty reads are mathematically impossible.

### 6.2. Transaction Log Mechanics (`_delta_log`)
Delta Lake achieves ACID via a transaction log directory named `_delta_log/` sitting at the root of the table.
- Every time Spark writes a batch, it creates a new JSON file (e.g., `00000000000000000001.json`).
- This JSON file acts as a manifest, detailing exactly which underlying Parquet files were added or removed in that transaction.
- When a BI engine queries the table, it first reads the `_delta_log`. It ignores any physical Parquet files in the bucket that are not explicitly listed as "valid" in the most recent commit.
- If a Spark job crashes mid-write, the physical files might be in the bucket, but because the JSON commit file was never created, the corrupted files are completely invisible to readers.

```json
// Example of a Delta Log Commit (00000000000000000001.json)
{
  "commitInfo": {
    "timestamp": 1713456789000,
    "operation": "WRITE",
    "operationParameters": {"mode": "Append"},
    "isolationLevel": "WriteSerializable",
    "isBlindAppend": true
  }
}
{
  "add": {
    "path": "part-00000-abcd-efgh.c000.snappy.parquet",
    "size": 10485760,
    "modificationTime": 1713456789000,
    "dataChange": true,
    "stats": "{\"numRecords\": 5000, \"minValues\": {\"id\": 1}, \"maxValues\": {\"id\": 5000}}"
  }
}
```

### 6.3. Time Travel and Auditability
Because Delta Lake maintains historical versions of the data (by keeping old JSON commit files and old Parquet files), the platform natively supports Time Travel.
Data Stewards can query older snapshots to debug upstream API corruption or replay failed machine learning models.
```sql
-- Query the state of the table exactly as it was 24 hours ago
SELECT * FROM prod_catalog.ethereum.gold TIMESTAMP AS OF current_timestamp() - INTERVAL 1 DAY;

-- Query a specific structural version of the table
SELECT * FROM prod_catalog.ethereum.gold VERSION AS OF 42;
```

### 6.4. The Small File Problem & Z-Ordering Optimization
Real-time streaming creates thousands of tiny files. Delta enables the `OPTIMIZE` command, which physically reads all the tiny 10KB files and rewrites them into massive, highly-compressed 1GB Parquet files.
Furthermore, we employ `ZORDER BY (id, timestamp)`. This algorithm physically colocates similar data in the same Parquet files on disk. When the Next.js dashboard queries for a specific timeframe, Spark uses the metadata in the `_delta_log` to instantly skip 99% of the Parquet files, reading only the exact blocks required.

---

## 7. Security & Governance: The Unity Catalog Pivot

A critical enterprise roadblock occurred during the initial implementation phase, requiring a massive architectural pivot.

### 7.1. The GCP IAM Roadblock
Standard cloud architecture patterns dictate that a local Python ingestion agent authenticates to a raw GCS landing bucket using a GCP Service Account JSON key (e.g., `credentials.json`).
However, the organization's CISO enforced a strict GCP Organization Policy: `iam.disableServiceAccountKeyCreation`. This mathematically prevented the generation of long-lived JSON keys. Without a key, the Python agent could not authenticate with Google Cloud, blocking all ingestion.

### 7.2. Bypassing Legacy IAM via Unity Catalog Volumes
Rather than requesting a highly privileged security exception, we dynamically pivoted the architecture to utilize **Databricks Unity Catalog Volumes**.
- A Unity Catalog Volume is a governed, logical construct within Databricks that physically maps to a GCS bucket.
- Instead of fighting GCP IAM, we bypassed it entirely. The Python agent uses the official Databricks SDK (`WorkspaceClient`) and authenticates via a Databricks Personal Access Token (PAT).
- Databricks Unity Catalog seamlessly handles the underlying IAM translation. The script writes directly to the Volume (`/Volumes/prod_catalog/.../raw_landing/`).
- This centralizes all governance within the Lakehouse. The GCP bucket is completely hidden from the developer; they only interact with Databricks.

### 7.3. RBAC and Token Lifecycle Management
By shifting authentication to Databricks PATs, we integrated deeply into Databricks Role-Based Access Control (RBAC).
- Tokens are scoped strictly to the `data_ingestion_service_principal`.
- Tokens have a forced 90-day expiration lifecycle, adhering to SOC2 compliance.
- All actions performed by the token are automatically audited in the Databricks Workspace Audit Logs, providing forensic traceability that raw GCS buckets lack.

---

## 8. Ingestion Mechanics: Auto Loader vs Traditional Spark

Ingesting data from object storage is surprisingly complex at scale. 

### 8.1. The O(N) Directory Listing Bottleneck
Traditional Spark Structured Streaming (`spark.readStream.json("gs://...")`) suffers from an algorithmic bottleneck. As millions of files accumulate in the raw bucket over months of streaming, Spark must execute an `ls` command to scan the entire directory tree on every micro-batch just to discover which files are "new". This $O(N)$ operation eventually brings the cluster to a halt, taking minutes just to list files before processing even begins.

### 8.2. Auto Loader RocksDB State Management
**The Decision:** All ingestion from the Volumes utilizes **Databricks Auto Loader (`cloudFiles`)**.
- Auto Loader circumvents directory listing entirely. It utilizes an embedded **RocksDB** key-value state store (persisted in the `_checkpoints/write` directory).
- As files land in the Volume, Auto Loader hashes their filenames and stores them in RocksDB in $O(1)$ time. 
- This guarantees exactly-once processing (a file is never processed twice) and ensures that ingestion latency remains perfectly flat, regardless of whether the bucket contains 1,000 files or 1,000,000,000 files.

```python
# Example Auto Loader Configuration used in production
df = spark.readStream.format("cloudFiles") \
    .option("cloudFiles.format", "json") \
    .option("cloudFiles.schemaLocation", "dbfs:/checkpoints/schema_inference") \
    .option("cloudFiles.inferColumnTypes", "true") \
    .option("cloudFiles.schemaEvolutionMode", "rescue") \
    .load("/Volumes/prod_catalog/ethereum/raw_landing/")
```

### 8.3. Schema Evolution Modes in Production
Upstream APIs break. Auto Loader provides multiple ways to handle this. We strictly utilize `schemaEvolutionMode: "rescue"`.
- If an API drops a column, Auto Loader fills it with `null`.
- If an API changes a data type (e.g., Integer to String), Auto Loader casts safely or routes to rescue.
- If an API adds a brand new nested JSON struct, Auto Loader does not crash. It captures the unmapped payload and dumps it into a stringified JSON column named `_rescued_data`. Data Engineers can later parse this column to extract the new feature without having suffered any downtime.

---

## 9. Infrastructure as Code & Deployment

While the current iteration utilizes local Python orchestration, the architecture is designed to be fully integrated into CI/CD pipelines via Databricks Asset Bundles (DABs) or Terraform.
- **Workspace Configuration:** All SQL Warehouses, Clusters, and Unity Catalog structures must be provisioned via Terraform to prevent configuration drift.
- **Job Definitions:** Databricks Workflows (if utilized in the future) should be defined in YAML and deployed via GitHub Actions.

---

## 10. Cost Projections & DBU Economics

The Lakehouse architecture is highly cost-efficient compared to traditional warehouses. Databricks bills in Databricks Units (DBUs).
- **Storage:** GCS Standard Storage is extremely cheap (~$0.02 per GB/month). Because Delta Lake stores data in GCS, our storage costs are fractional compared to Snowflake's marked-up storage.
- **Compute:** By utilizing Serverless Compute with `AvailableNow=True` micro-batching, we only pay for the exact seconds the cluster is actively processing data. Idle time is billed at $0.00. 
- **SQL Warehouse:** The Next.js dashboard queries a Serverless SQL Warehouse. Because it queries the highly-optimized Gold tables, queries execute in milliseconds, keeping the warehouse in a low-consumption state and allowing aggressive auto-termination (e.g., 5 minutes of inactivity shuts down the warehouse).

---

## 11. Disaster Recovery & Business Continuity

- **RPO (Recovery Point Objective):** Near-zero. Because raw data lands in GCS (which has 11 nines of durability), even if the entire Databricks workspace is deleted, the raw data remains safe.
- **RTO (Recovery Time Objective):** < 15 minutes. In the event of catastrophic workspace failure, a new workspace can be spun up via Terraform, Unity Catalog re-attached to the GCS bucket, and the `AvailableNow` streams restarted. Auto Loader will read its RocksDB state and instantly resume from the exact file it left off at.

---

## 12. Comprehensive FAQ

**Q: Why not use Apache Kafka or Confluent for ingestion?**
A: Kafka is excellent for true millisecond-latency streaming. However, it requires managing a complex broker infrastructure and has strict retention limits (data expires after X days). By streaming directly to Unity Catalog Volumes, we use cheap object storage as an infinite-retention message queue, which is far more cost-effective for our latency requirements.

**Q: If we use Databricks PATs, what happens if the developer leaves the company?**
A: The PATs used in production must belong to a Databricks Service Principal, not an individual user. Service Principals are non-human accounts designed for automated workloads, ensuring the pipeline doesn't break during employee offboarding.

**Q: How does this architecture handle GDPR Right to be Forgotten requests?**
A: Delta Lake natively supports standard `DELETE` and `UPDATE` SQL commands. A Data Steward can execute `DELETE FROM prod_catalog.silver WHERE user_id = '123'`. Delta Lake will dynamically rewrite the underlying Parquet files to physically purge the data to comply with GDPR/CCPA.

---

## 13. Glossary of Terms

- **ACID:** Atomicity, Consistency, Isolation, Durability. The bedrock of reliable database transactions.
- **DBU:** Databricks Unit. The metric used by Databricks to bill for compute usage.
- **Dead Letter Queue (DLQ):** A routing mechanism to isolate malformed or toxic data that fails schema or constraint validation, preventing it from crashing the main processing pipeline.
- **IAM:** Identity and Access Management. The security framework for controlling access to cloud resources.
- **Parquet:** An open-source, columnar storage file format highly optimized for analytical queries.
- **RocksDB:** An embedded key-value store optimized for fast storage environments, used by Databricks to manage streaming state.
- **Tungsten Engine:** The execution engine inside Apache Spark that optimizes memory and CPU usage at the bare-metal level.
- **Z-Ordering:** A technique to colocate related information in the same set of files, massively reducing the amount of data read during a query.

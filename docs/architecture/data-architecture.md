# Data Architecture: Multi-Dataset Medallion Lakehouse

This document outlines the data architecture for the Enterprise Databricks Lakehouse, specifically highlighting the real-time processing of our three global datasets: **Ethereum Web3, GitHub Archive, and Overture Maps**.

## 1. The Medallion Architecture

We employ a strict Bronze-Silver-Gold (Medallion) architecture implemented via Databricks Structured Streaming, Auto Loader, and Delta Lake. This ensures that data is progressively cleansed, enriched, and aggregated as it flows through the lakehouse, providing immutable audit trails at every layer.

```mermaid
flowchart LR
    A[Unity Catalog Volumes\nRaw JSON] -->|Auto Loader\n(Stream)| B[(Bronze Layer\nRaw Delta)]
    B -->|Structured Streaming\n+ Quality Rules| C[(Silver Layer\nCleansed Delta)]
    C -->|Batch Rollups\nAggregations| D[(Gold Layer\nBusiness Delta)]
    
    B -.->|Bad Data / Boundary Violations| E[(Quarantine Table)]
```

### Raw Landing Zone (Unity Catalog Volumes)
- **Source:** Databricks Unity Catalog Volumes (`/Volumes/prod_catalog/.../raw_landing/`) physically backed by Google Cloud Storage.
- **Mechanism:** Python API Ingestion Agent leveraging the Databricks SDK.
- **Reasoning:** Bypasses strict GCP IAM Service Account creation restrictions by relying on Databricks Personal Access Tokens (PAT) for auth.

### Bronze Layer (Raw Ingestion)
- **Mechanism:** Databricks Auto Loader (`cloudFiles`).
- **Goal:** Ingest data exactly as it arrives without modification, guaranteeing exactly-once processing via RocksDB state stores and Delta checkpoints (`_checkpoints/write`).
- **Evolution:** We utilize `schemaEvolutionMode` to dynamically handle API drifts. For Ethereum, we use `rescue` to dump unexpected columns into a `_rescued_data` column. 

### Silver Layer (Cleansing & Conforming)
- **Source:** Bronze Delta Tables (Stream).
- **Mechanism:** PySpark Structured Streaming with centralized Data Quality enforcement.
- **Validation Rules:** 
  - Overture Maps: Latitudes must be between -90 and 90, Longitudes between -180 and 180.
- **Deduplication:** Enforced via `.withWatermark("_ingested_at", "1 hour").dropDuplicates(["id", "_ingested_at"])`.
- **Quarantine (Dead Letter Queue):** Records failing fatal rules are instantly split from the Silver stream and routed to `prod_catalog.quality.quarantine` along with a `_quarantine_failed_rules` metadata reason. The Silver layer is guaranteed to contain 100% compliant data.

### Gold Layer (Business Aggregations)
- **Source:** Silver Delta Tables (Batch).
- **Mechanism:** Spark SQL Rollup aggregations executing post-stream (`update_gold_layer()`).
- **Output:** Highly denormalized, analytics-ready views optimized for the Next.js Command Center and BI tools. 
  - Ethereum: Total ETH Transferred, Average Gas Utilized.
  - GitHub: Global push event density by organization.
  - Overture: Categorized geographic mapping metrics.

## 2. Infrastructure & Storage
- **Underlying Provider:** Google Cloud Platform (GCP)
- **GCS Storage:** Google Cloud Storage acts as the physical persistence layer for all Unity Catalog Delta Tables and Volumes.
- **Unity Catalog (UC):** Centralized governance. All tables are created within `prod_catalog.<schema_name>.<table_name>`. 

## 3. Streaming Paradigms (Serverless Optimization)
- True 24/7 continuous processing (`ProcessingTime`) incurs massive idle cloud costs and is restricted on Databricks Serverless compute.
- **Micro-Batching Optimization:** The pipeline architecture relies entirely on **`AvailableNow=True`** triggers. We achieve "near real-time" capabilities by wrapping these micro-batch triggers in a native Python `while True:` loop inside the Master Notebook. This processes all pending files in the Volume instantly, commits the ACID transaction, and safely terminates the stream, optimizing compute utilization while remaining Serverless-compliant.

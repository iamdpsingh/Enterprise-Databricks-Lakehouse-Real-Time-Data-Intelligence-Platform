# Data Architecture: Multi-Dataset Medallion Lakehouse

This document outlines the data architecture for the Enterprise Databricks Lakehouse, specifically highlighting the real-time processing of our three global datasets: **Ethereum Web3, GitHub Archive, and Overture Maps**.

## 1. The Medallion Architecture

We employ a strict Bronze-Silver-Gold (Medallion) architecture implemented via Databricks Structured Streaming, Auto Loader, and Delta Lake. This ensures that data is progressively cleansed, enriched, and aggregated as it flows through the lakehouse, providing immutable audit trails at every layer.

```mermaid
flowchart LR
    A[GCP Cloud Storage\nRaw JSON] -->|Auto Loader\n(Stream)| B[(Bronze Layer\nRaw Delta)]
    B -->|Structured Streaming\n+ Quality Rules| C[(Silver Layer\nCleansed Delta)]
    C -->|Watermarked Window\nAggregations| D[(Gold Layer\nBusiness Delta)]
    
    B -.->|Bad Data| E[(Quarantine Table)]
```

### Bronze Layer (Raw Ingestion)
- **Source:** Google Cloud Storage (`gs://databrick-project-510903-raw-landing-zone/`)
- **Mechanism:** Databricks Auto Loader (`cloudFiles`).
- **Goal:** Ingest data exactly as it arrives without modification. 
- **Evolution:** We utilize `schemaEvolutionMode` to dynamically handle API drifts. For Ethereum, we use `rescue` to dump unexpected columns into a `_rescued_data` column. For GitHub, we use `addNewColumns` to proactively append new fields to the schema natively.

### Silver Layer (Cleansing & Conforming)
- **Source:** Bronze Delta Tables (Stream).
- **Mechanism:** PySpark Structured Streaming with a centralized Data Quality framework.
- **Validation Rules:** 
  - Ethereum: `hash` is not null; `gas` > 0.
  - GitHub: `repo_name` matches standard `<org>/<repo>` regex.
  - Overture: Latitudes must be between -90 and 90, Longitudes between -180 and 180.
- **Quarantine (Dead Letter Queue):** Records failing fatal rules are instantly routed to a separate `quality.quarantine` table along with the `_quarantine_failed_rules` metadata reason. The Silver layer is guaranteed to contain 100% compliant data.

### Gold Layer (Business Aggregations)
- **Source:** Silver Delta Tables (Stream).
- **Mechanism:** Spark SQL Tumbling window aggregations.
- **Output:** Analytics-ready views optimized for the Next.js Command Center and BI tools. 
  - Ethereum: Total ETH Transferred, Transaction Velocity.
  - GitHub: Global push event density by organization.
  - Overture: Categorized geographic mapping metrics.

## 2. Infrastructure & Storage
- **GCP Project:** `databrick-project-510903`
- **GCS Storage:** Google Cloud Storage acts as the physical persistence layer for all Unity Catalog Delta Tables.
- **Unity Catalog (UC):** Centralized governance. All tables are created within `prod_catalog.<schema_name>.<table_name>`. UC handles ACL permissions and cross-workspace sharing dynamically.

## 3. Streaming Paradigms
- The architecture favors **Continuous Processing** for low-latency dashboards (trigger="processingTime").
- To optimize cloud costs, pipelines can easily be swapped to **Trigger.AvailableNow()**, processing all pending files in the GCS bucket in micro-batches before shutting down the cluster.

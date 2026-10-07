# Data Architecture: Medallion Lakehouse

This document outlines the data architecture for the Enterprise Databricks Lakehouse, specifically highlighting the real-world scale processing of **146 Million NYC Taxi Trips**.

## 1. The Medallion Architecture

We employ a strict Bronze-Silver-Gold (Medallion) architecture implemented via Databricks Structured Streaming and Delta Lake.

```mermaid
flowchart LR
    A[GCS Bucket\nRaw Parquet] -->|Auto Loader\n(Stream)| B[(Bronze\nRaw Delta)]
    B -->|Structured Streaming\n+ Quality Rules| C[(Silver\nCleansed Delta)]
    C -->|Watermarked Window\nAggregations| D[(Gold\nBusiness Delta)]
    
    B -.->|Bad Data| E[(Quarantine)]
```

### Bronze Layer (Raw Ingestion)
- **Source:** Google Cloud Storage (`gs://databrick-project-510903-data/landing/nyc_taxi_2015/`)
- **Volume:** ~146M records across 203 parquet files.
- **Mechanism:** Databricks Auto Loader (`cloudFiles`).
- **Goal:** Ingest data exactly as it arrives without modification. Appends `_ingested_at` metadata. Schema evolution is set to `rescue`.

### Silver Layer (Cleansing & Conforming)
- **Source:** Bronze Delta Table (Stream).
- **Mechanism:** PySpark Structured Streaming with centralized `QualityRule` framework.
- **Validation:** 
  - `passenger_count > 0`
  - `fare_amount >= 0`
  - `trip_distance >= 0`
  - Required fields are non-null.
- **Quarantine:** Records failing fatal rules are routed to a separate `quarantine_trips` table along with the `_failed_rules` metadata.

### Gold Layer (Business Aggregations)
- **Source:** Silver Delta Table (Stream).
- **Mechanism:** Watermarked tumbling window aggregations (1-hour windows).
- **Output:** Hourly aggregations by `pickup_location_id` featuring:
  - Total Revenue
  - Total Trips
  - Average Distance
  - Total Passengers
- **SLA:** Near real-time streaming updates.

## 2. Infrastructure & Storage
- **GCP Project:** `databrick-project-510903`
- **GCS Storage:** Used for landing zones and Delta Lake external locations.
- **Unity Catalog:** Centralized governance for all tables, managing access controls across Dev, Staging, and Prod workspaces.

## 3. Orchestration
- Orchestrated via **Databricks Workflows (Jobs)** defined as Infrastructure-as-Code using **Databricks Asset Bundles (DABs)** (`databricks.yml`).
- Cluster definitions are standardized using `n2-standard-4` instances.

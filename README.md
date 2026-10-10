# 🌌 Enterprise Databricks Lakehouse & Real-Time Data Intelligence Platform

![Architecture](https://img.shields.io/badge/Architecture-Medallion-blue.svg)
![Platform](https://img.shields.io/badge/Compute-GCP_|_Databricks-orange.svg)
![UI](https://img.shields.io/badge/Frontend-Next.js_14-black.svg)
![Orchestration](https://img.shields.io/badge/Orchestration-Apache_Airflow-lightgrey.svg)

An industrial-scale, production-grade data platform built on **Databricks** and **Google Cloud Platform (GCP)**. This platform implements a strict **Medallion Architecture** managed by **Unity Catalog** to process, clean, and serve over **20 Billion records** from four massive global datasets.

A state-of-the-art **Next.js Command Center** provides real-time telemetry, data quality metrics, and pipeline health observability.

---

## 🚀 Core Architecture & Compute

> **Strict Compute Rule:** All computational work, data processing, and pipeline execution is isolated entirely to **Google Cloud Platform (GCP)**. Absolutely no computational heavy-lifting occurs on local environments.

*   **Ingestion (Bronze):** Databricks Auto Loader (`cloudFiles`) and custom REST API clients ingest raw JSON/Parquet into GCP Landing Zones (`gs://`).
*   **Processing (Silver):** PySpark structured streaming handles deduplication, PII masking, schema evolution, and Slowly Changing Dimensions (SCD Type 2). 
*   **Aggregation (Gold):** Highly optimized Delta tables serve business-level aggregations and machine-learning ready datasets.
*   **Infrastructure:** GCP resources (GCS buckets, Artifact Registry) are managed via **Terraform** (`dev`, `staging`, `prod`).

---

## 📊 The 4 Global Datasets

This platform natively parallel-processes four distinct, high-velocity datasets:

### 1. 🦇 Ethereum Web3
*   **Ingestion:** Auto Loader with `schemaEvolutionMode: "rescue"` to handle dynamic smart contract events.
*   **Transformations:** Complex Hex-to-Long decoding of `gas` and transaction `value` during Silver processing.
*   **Gold Metrics:** Daily ETH transferred, average gas utilized, and wallet activity trends.

### 2. 🐙 GitHub Archive
*   **Ingestion:** Auto Loader with `schemaEvolutionMode: "addNewColumns"` for highly nested, evolving JSON events.
*   **Transformations:** Unpacking deeply nested structs and enforcing strict row deduplication.
*   **Gold Metrics:** Daily repository event velocity and global developer activity.

### 3. 🗺️ Overture Maps
*   **Ingestion:** High-throughput Parquet ingestion via Auto Loader.
*   **Transformations:** Strict geospatial boundary validations (Lat/Lon filtering).
*   **Gold Metrics:** Point of Interest (POI) categorization and global region mapping.

### 4. 💬 Reddit Pushshift
*   **Ingestion:** Custom resilience-focused `RestApiReader` polling live submission APIs.
*   **Transformations:** HTML stripping, **PII Masking** (Email pseudonymization), and historical state tracking via **SCD Type 2 CDC**.
*   **Gold Metrics:** Subreddit sentiment, posting volume, and average community scores.

---

## 🛡️ Enterprise Data Quality & Quarantine

Built with a robust, highly extensible PySpark Data Quality engine:

*   **Rule Engine:** Enforces `is_not_null`, Regex pattern matching, and complex Window-based uniqueness constraints (`rule_is_unique`).
*   **Quarantine Flow:** Records failing fatal constraints (e.g., invalid geospatial coordinates) are automatically routed to a dedicated `quality.quarantine` Delta table for review, ensuring the Silver layer remains pristine.
*   **Testing:** Comprehensive **PyTest** suites utilize isolated local Delta-Spark sessions to validate CDC and Data Quality pipelines as part of the CI process.

---

## 🕹️ Next.js Command Center (Monitoring UI)

A premium, state-of-the-art Web Application for monitoring the Lakehouse.
*   **Tech Stack:** Next.js 14, React, Vanilla CSS (Glassmorphism), `framer-motion` for micro-animations.
*   **Features:** Features 4 dedicated dashboard sections reflecting real-time row counts, streaming ingestion rates, and compute node health directly from the Databricks backend.

To run the UI locally:
```bash
cd monitoring-ui
npm install
npm run dev
```

---

## ⚙️ Orchestration & CI/CD

### Airflow
Pipelines are orchestrated via **Apache Airflow** (`src/orchestration/airflow/dags/lakehouse_pipeline.py`).
The DAG dynamically fans out to process all 4 datasets in parallel on Databricks Serverless, passing environment-specific `notebook_params` and enforcing a strict Data Quality Gate.

### GitHub Actions
*   **CI (`ci.yml`):** Runs the PyTest Medallion test suite on all PRs.
*   **CD (`cd-prod.yml`):** Deploys Databricks assets via the Databricks CLI (`bundle deploy`) and pushes the Next.js UI to Vercel.

---

## 📂 Repository Structure

```text
├── .github/workflows/          # CI/CD Pipelines
├── infrastructure/terraform/   # GCP IaC (dev, staging, prod)
├── monitoring-ui/              # Next.js Command Center App
├── sql/                        # Unity Catalog DDL (create_tables.sql)
├── src/
│   ├── cdc/                    # SCD Type 2 logic
│   ├── ingestion/              # AutoLoader & API Clients
│   ├── orchestration/          # Airflow DAGs
│   ├── pipelines/              # Medallion pipelines (eth, github, overture, reddit)
│   ├── quality/                # DQ Rules & Quarantine logic
│   └── transformations/        # PII masking & text cleaning
└── tests/unit/                 # PyTest suites (Delta Lake local session)
```

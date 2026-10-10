# Enterprise Databricks Lakehouse & Real-Time Data Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **industrial-scale, production-grade data intelligence platform** built on Databricks and GCP (Project: `databrick-project-510903`). This project demonstrates enterprise data engineering best practices processing **4 Global Datasets (Ethereum Web3, GitHub Archive, Overture Maps, Reddit Pushshift) totaling over 20 Billion records**. All computational workloads are strictly isolated to **GCP compute resources**. Operations are commanded remotely from a developer laptop, ensuring absolutely **zero local computation**. Features Medallion architecture, Unity Catalog governance, real-time streaming, automated data quality, and full operational observability via a Next.js command center.

---

## 🏗️ Architecture Overview

```
Developer Laptop (Zero Local Computation)
  └── Databricks CLI / Remote Execution
        └── GCP (Foundation)
              ├── Cloud Storage (Landing Zone)
              ├── Secret Manager
              └── Artifact Registry (Docker)
        └── Databricks (Data Engine on GCP)
              ├── Unity Catalog (Governance)
              ├── Bronze → Silver → Gold (Medallion)
              ├── Structured Streaming
              └── Lakeflow Pipelines
```

---

## 🛠️ Technology Stack

| Category | Technology |
|----------|-----------|
| Cloud | Google Cloud Platform |
| Lakehouse | Databricks |
| Processing | Apache Spark / PySpark |
| Storage | GCS + Delta Lake |
| Governance | Unity Catalog |
| Streaming | Structured Streaming |
| Ingestion | Auto Loader / APIs / Batch |
| Pipelines | Lakeflow |
| Orchestration | Databricks Workflows / Apache Airflow |
| CDC | Delta CDF / MERGE (SCD Type 2) |
| Infrastructure | Terraform |
| Frontend | Next.js 14 + TypeScript + Framer Motion |
| BI | Power BI |
| Documentation | Markdown + Mermaid + ADRs |

---

## 📊 The 4 Global Datasets

This platform is specifically tuned to ingest and transform four massive, real-time datasets.

### 1. 🦇 Ethereum Web3
*   **Ingestion:** Auto Loader with `schemaEvolutionMode: "rescue"` to safely handle unexpected smart contract events.
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

---

## 📁 Repository Structure

```
├── databricks/                 # Asset Bundles, notebooks, pipeline definitions
├── src/                        # Production Python source code
│   ├── ingestion/              # Auto Loader and API ingestion modules
│   ├── transformations/        # Bronze → Silver → Gold transformations
│   ├── pipelines/              # Orchestrated dataset pipelines (ethereum, github, etc.)
│   ├── streaming/              # Structured Streaming jobs
│   ├── cdc/                    # Change Data Capture merge patterns
│   ├── quality/                # Data quality validation framework
│   └── utilities/              # Shared helpers: config, logging, retry
├── sql/                        # DDL for Bronze, Silver, and Gold tables (create_tables.sql)
├── infrastructure/             # Terraform (GCP + Databricks), Docker
├── monitoring/                 # Alert rules, metric definitions, dashboards
├── monitoring-ui/              # Next.js Data Platform Control Center
├── configs/                    # Environment-specific configurations
├── data-contracts/             # Formal contracts for Gold data products
├── docs/                       # Full project documentation
└── ADR/                        # Architecture Decision Records
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 20+
- GCP CLI (`gcloud`)
- Databricks CLI (`databricks`)
- Terraform 1.6+

### Local Environment Setup

```bash
# 1. Clone the repository
git clone https://github.com/iamdpsingh/Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform.git
cd Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform

# 2. Configure Databricks CLI (Authenticates your laptop to GCP Databricks)
databricks configure --token
# Enter your GCP Databricks Host and Token when prompted.
```

---

## 🧪 Validating the Project is Working

You can verify that the core processing engine, data quality rules, and front-end command center are completely functional by following these steps:

### 1. Execute Remote Pipelines (Zero Local Compute)
Trigger the Medallion pipelines remotely using the Databricks CLI. All computation runs exclusively on GCP.
```bash
# Deploy and run the pipeline bundle on GCP Databricks
databricks bundle deploy -t prod
databricks bundle run orders_pipeline -t prod
```

### 2. Verify Airflow DAG Orchestration
Ensure the Airflow orchestration is structured properly without parsing errors.
```bash
python3 src/orchestration/airflow/dags/lakehouse_pipeline.py
```
**Expected Output:** Exits quietly with code `0` (no output means the DAG compiled successfully).

### 3. Run the Next.js Command Center (Monitoring UI)
Launch the premium glassmorphism command center locally to view the real-time dashboard reflecting the state of the 4 datasets running on GCP.

```bash
cd monitoring-ui
npm install
npm run dev
```
**Expected Output:** The UI will be available at `http://localhost:3000`. Navigate through the sidebar to view the beautifully animated, dataset-specific telemetry pages.

---

## 🔄 Operations Workflow (Remote Execution)

1. **Write Code Locally:** Develop pipeline logic (`src/`) and SQL definitions (`sql/`) in your local IDE.
2. **Authenticate:** Ensure Databricks CLI is configured to point to your GCP workspace.
3. **Deploy to GCP:** Run `databricks bundle deploy` to sync your local code to the remote workspace.
4. **Execute on GCP:** Run `databricks bundle run` to trigger the jobs. **Absolutely zero data processing or Spark execution happens on your laptop.**
5. **Monitor UI:** Open the Next.js Command Center to observe the remote cluster telemetry and data flow.

---

## 📖 Documentation

Full documentation is available in the [`docs/`](./docs/) directory:

- [System Architecture](./docs/architecture/system-architecture.md)
- [Data Architecture](./docs/architecture/data-architecture.md)
- [Operations Runbook](./docs/operations/runbook.md)
- [Architecture Decision Records](./ADR/)

---

## 🔒 Security

Please see [SECURITY.md](./SECURITY.md) for the vulnerability reporting process and security policies.

---

## 🤝 Contributing

Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for our contribution guidelines and coding standards.

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

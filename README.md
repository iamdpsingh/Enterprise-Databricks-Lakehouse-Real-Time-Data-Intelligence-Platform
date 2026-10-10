# Enterprise Databricks Lakehouse & Real-Time Data Intelligence Platform

[![CI](https://github.com/iamdpsingh/Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/iamdpsingh/Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **industrial-scale, production-grade data intelligence platform** built on Databricks, GCP (Project: `databrick-project-510903`), and GitHub Actions CI/CD. This project demonstrates enterprise data engineering best practices processing **4 Global Datasets (Ethereum Web3, GitHub Archive, Overture Maps, Reddit Pushshift) totaling over 20 Billion records**. All computational workloads are strictly isolated to **GCP compute resources**—no local processing is performed. Features Medallion architecture, Unity Catalog governance, real-time streaming, automated data quality, and full operational observability via a Next.js command center.

---

## 🏗️ Architecture Overview

```
Developer Laptop
  └── Git Push / PR
        └── GitHub (Control Plane)
              ├── CI — Lint / Test / Scan / Validate
              └── CD — Deploy to GCP + Databricks
                    ├── GCP (Foundation)
                    │     ├── Cloud Storage (Landing Zone)
                    │     ├── Secret Manager
                    │     ├── Artifact Registry (Docker)
                    │     └── Cloud Run (Containerized Services)
                    └── Databricks (Data Engine)
                          ├── Unity Catalog (Governance)
                          ├── Bronze → Silver → Gold (Medallion)
                          ├── Structured Streaming
                          ├── Lakeflow Pipelines
                          └── MLflow
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
| ML Lifecycle | MLflow |
| Containers | Docker → GCP Artifact Registry |
| Infrastructure | Terraform |
| Version Control | Git + GitHub |
| CI/CD | GitHub Actions |
| Frontend | Next.js 14 + TypeScript + Framer Motion |
| Testing | Pytest + Data/Pipeline Tests |
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
*   **Testing:** Comprehensive **PyTest** suites utilize isolated local Delta-Spark sessions to validate CDC and Data Quality pipelines as part of the CI process.

---

## 📁 Repository Structure

```
├── .github/                    # CI/CD workflows, PR templates, CODEOWNERS
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
├── tests/                      # Unit, integration, data quality, performance
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
- Docker

### Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/iamdpsingh/Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform.git
cd Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform

# 2. Install Python dependencies (using uv or pip)
pip install -e ".[dev]"
pip install pytest pyspark delta-spark # Required for unit tests

# 3. Install pre-commit hooks
pre-commit install
```

---

## 🧪 Validating the Project is Working

You can verify that the core processing engine, data quality rules, and front-end command center are completely functional by following these steps:

### 1. Run the Pipeline Unit Tests
The Medallion pipelines and Data Quality quarantine flows are covered by comprehensive isolated PyTest suites using local Delta Lake.

```bash
# Run the test suite
pytest tests/unit/ -v
```
**Expected Output:** All tests should pass (green), confirming that PII masking, SCD Type 2 CDC tracking, schema evolution configurations, and quarantine routing logic execute flawlessly.

### 2. Verify Airflow DAG Orchestration
Ensure the Airflow orchestration is structured properly without parsing errors.
```bash
python3 src/orchestration/airflow/dags/lakehouse_pipeline.py
```
**Expected Output:** Exits quietly with code `0` (no output means the DAG compiled successfully).

### 3. Run the Next.js Command Center (Monitoring UI)
Launch the premium glassmorphism command center locally to view the real-time dashboard reflecting the state of the 4 datasets.

```bash
cd monitoring-ui
npm install
npm run dev
```
**Expected Output:** The UI will be available at `http://localhost:3000`. Navigate through the sidebar to view the beautifully animated, dataset-specific telemetry pages (`/ethereum`, `/github`, `/overture`, `/reddit`).

---

## 🔄 Development Workflow

1. **Create an issue** in GitHub for the work you are doing.
2. **Create a feature branch**: `git checkout -b feature/<issue-id>-short-description`
3. **Write code + tests** following the standards in `.agents/rules/`.
4. **Commit atomically** — one logical change per commit.
5. **Open a Pull Request** — link to the issue, fill the PR template.
6. **CI passes** — all gates must be green before merge.
7. **PR is reviewed** — at least 1 approval required.
8. **Merge to develop** → **CD deploys to Dev** → promote to Staging → Production.

---

## 📖 Documentation

Full documentation is available in the [`docs/`](./docs/) directory:

- [System Architecture](./docs/architecture/system-architecture.md)
- [Data Architecture](./docs/architecture/data-architecture.md)
- [CI/CD Strategy](./docs/cicd/strategy.md)
- [Testing Guide](./docs/testing/unit-testing.md)
- [Operations Runbook](./docs/operations/runbook.md)
- [Architecture Decision Records](./ADR/)

---

## 🔒 Security

Please see [SECURITY.md](./SECURITY.md) for the vulnerability reporting process and security policies.

---

## 🤝 Contributing

Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for our contribution guidelines, coding standards, and PR process.

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

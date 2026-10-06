# Enterprise Databricks Lakehouse & Real-Time Data Intelligence Platform

[![CI](https://github.com/iamdpsingh/Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/iamdpsingh/Enterprise-Databricks-Lakehouse-Real-Time-Data-Intelligence-Platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **industrial-scale, production-grade data intelligence platform** built on Databricks, GCP, and GitHub Actions CI/CD. This project demonstrates enterprise data engineering best practices including Medallion architecture, Unity Catalog governance, real-time streaming, automated data quality, and full operational observability.

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
| Orchestration | Databricks Workflows |
| CDC | Delta CDF / MERGE |
| ML Lifecycle | MLflow |
| Containers | Docker → GCP Artifact Registry |
| Infrastructure | Terraform |
| Version Control | Git + GitHub |
| CI/CD | GitHub Actions |
| Frontend | Next.js + TypeScript |
| Testing | Pytest + Data/Pipeline Tests |
| BI | Power BI |
| Documentation | Markdown + Mermaid + ADRs |

---

## 📁 Repository Structure

```
├── .github/                    # CI/CD workflows, PR templates, CODEOWNERS
├── databricks/                 # Asset Bundles, notebooks, pipeline definitions
├── src/                        # Production Python source code
│   ├── ingestion/              # Auto Loader and API ingestion modules
│   ├── transformations/        # Bronze → Silver → Gold transformations
│   ├── streaming/              # Structured Streaming jobs
│   ├── cdc/                    # Change Data Capture merge patterns
│   ├── quality/                # Data quality validation framework
│   └── utilities/              # Shared helpers: config, logging, retry
├── sql/                        # DDL for Bronze, Silver, and Gold tables
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

# 3. Install pre-commit hooks
pre-commit install

# 4. Verify setup — run linting and unit tests
ruff check .
pytest tests/unit/ -v

# 5. Set up Next.js monitoring UI
cd monitoring-ui
npm install
npm run dev
```

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

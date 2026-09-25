# Production Engineering Principles

## 1. Automation First
**Nothing important is manual if it can reasonably be automated.**
- Infrastructure must be provisioned via Terraform.
- Deployments must be executed via GitHub Actions.
- Testing must be automated in CI.
- Routine maintenance (e.g., Delta table OPTIMIZE/VACUUM) must be scheduled via Workflows.
- Data quality checks must be automated pipeline steps.

## 2. Reliability & Resilience
- **Idempotency:** Pipelines must be able to run multiple times without causing data duplication or corruption.
- **Checkpointing:** Streaming jobs must use reliable checkpointing in GCS.
- **Retries:** Ephemeral failures (network glitches, API limits) must be handled with exponential backoff retries.
- **Atomic Writes:** Use Delta Lake's ACID transactions to ensure writes are all-or-nothing.
- **Graceful Degradation:** The Next.js dashboard should continue to function (perhaps with cached data) if backend systems are temporarily unavailable.

## 3. Scalability
- **Distributed Processing:** Leverage PySpark for heavy computation. Do not use local Pandas unless operating on significantly reduced/aggregated data.
- **Partitioning:** Implement logical partitioning strategies on large Delta tables to optimize read performance.
- **Incremental Processing:** Prefer incremental processing (Structured Streaming, CDF) over full table recalculations for large datasets.
- **Right-Sizing:** Configure auto-scaling on Databricks clusters and GKE/Cloud Run deployments to match workload demands dynamically.

## 4. Security & Governance (Defense in Depth)
- **Least Privilege:** Service accounts and users must only have the permissions strictly necessary for their role.
- **Zero Hardcoded Secrets:** All credentials, API keys, and sensitive configs must be stored in GCP Secret Manager or GitHub Secrets.
- **Unified Governance:** Unity Catalog is the single source of truth for data access controls (table, row, and column level).
- **Auditability:** All systems (GCP, Databricks, GitHub) must have audit logging enabled and monitored.

## 5. Observability (Design for Debuggability)
- **Comprehensive Telemetry:** Collect metrics, logs, and traces across all components (Infrastructure, Data Platform, Data).
- **Actionable Alerts:** Alerts should only fire for actionable issues. Fatigue is a risk.
- **Centralized Dashboard:** The Next.js Data Platform Control Center must provide a single pane of glass for system health, data quality, and lineage.

## 6. Maintainability (Code as a Craft)
- **Modular Design:** Break complex pipelines into smaller, testable, and reusable Python modules or SQL models.
- **Configuration-Driven:** Extract environment-specific variables and pipeline parameters into configuration files (YAML/JSON).
- **Clean Code:** Follow strict linting, formatting, and typing rules (Ruff, Mypy, ESLint, Prettier).
- **Test-Driven:** Write tests (unit, integration, data) before or alongside the code.

## 7. DevOps Culture
- **Shift Left:** Security scanning, linting, and testing happen locally and in CI, long before deployment.
- **Environment Parity:** Dev, Staging, and Prod must be as identical as possible in configuration and architecture.
- **Continuous Improvement:** Post-mortems are blameless and focus on systemic improvements.

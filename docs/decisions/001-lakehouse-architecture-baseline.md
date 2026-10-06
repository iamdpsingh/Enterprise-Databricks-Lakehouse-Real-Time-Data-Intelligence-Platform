# ADR-001: Databricks Lakehouse Architecture Baseline

## Status
Accepted

## Context
We are building the "Enterprise Databricks Lakehouse & Real-Time Data Intelligence Platform" on GCP. The platform must be strictly governed, fully documented, observable, and automated via GitOps. We need to decide on the core foundational architecture, specifically how we manage infrastructure, code, and deployments.

## Decision
We will adopt the following foundational architecture:
1. **Infrastructure as Code (IaC) & Deployment:** Databricks Asset Bundles (DABs) will be used to deploy Databricks resources (Jobs, DLT pipelines, models). No resources will be created manually via the UI.
2. **Compute Engine:** Databricks on GCP will serve as the core compute engine for heavy transformations.
3. **Storage:** Google Cloud Storage (GCS) interacting with Unity Catalog via External Locations. All data will be stored in the open Delta Lake format.
4. **Data Modeling:** Medallion Architecture (Bronze, Silver, Gold).
    *   **Bronze:** Raw, untransformed data. Ingested via Auto Loader for streaming cloud files.
    *   **Silver:** Cleaned, deduplicated (SCD1/SCD2), and statically masked data.
    *   **Gold:** Business-level aggregations and dimensional models.
5. **CI/CD:** GitHub Actions will be the orchestrator. Workload Identity Federation (WIF) will be used to authenticate with GCP/Databricks without static service account keys.
6. **Data Quality:** Handled natively in pipeline stages using a combination of DLT expectations and a custom Quarantine splitting mechanism (`QuarantineManager`).
7. **Observability:** Centralized JSON-formatted logging via `structlog`. Next.js dashboard for custom metric visualization.
8. **Security & Governance:** Unity Catalog handles access control (RBAC). Secrets managed in GCP Secret Manager / Databricks Secrets.

## Consequences
**Positive:**
*   **Reproducibility:** The entire platform can be torn down and rebuilt from the Git repository.
*   **Security:** WIF eliminates long-lived credentials.
*   **Scalability:** Delta Lake and Spark provide limitless scale for both batch and streaming.

**Negative:**
*   **Learning Curve:** Developers must understand DABs, WIF, and strictly adhere to the GitOps workflow. Local testing requires bridging to a Databricks cluster (e.g., Databricks Connect).
*   **Overhead:** Enforcing atomic commits and strict CI checks slows down initial "quick and dirty" prototyping.

## References
*   Project 6 Master Architecture Document
*   Databricks Asset Bundles Documentation

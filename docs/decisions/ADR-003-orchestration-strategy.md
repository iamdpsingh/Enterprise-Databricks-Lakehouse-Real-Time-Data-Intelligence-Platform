# ADR 003: Pipeline Orchestration Strategy

## Status
Accepted

## Context
An enterprise platform requires a robust orchestration engine to schedule batch jobs, trigger streaming pipelines, and manage the dependency graph between the Bronze, Silver, and Gold transformations. While tools like Apache Airflow are standard, managing an external Airflow cluster on GCP adds significant infrastructure overhead, IAM complexity, and network latency when triggering Databricks clusters.

## Decision
We will utilize **Databricks Workflows (Jobs)** natively integrated with the workspace, and define all infrastructure as code (IaC) using **Databricks Asset Bundles (DABs)**.

### Core Paradigms:
1. **Asset Bundles (`databricks.yml`):** All pipeline definitions, cluster configurations, and schedules will be declared in YAML format locally.
2. **Remote Execution:** Developers will use the Databricks CLI (`databricks bundle deploy` and `databricks bundle run`) to sync their local code to GCP and execute it on cloud compute. Zero data processing happens on the developer laptop.
3. **Task Dependencies:** Workflows will define strict linear DAGs (e.g. `ethereum_bronze_task` -> `ethereum_silver_task` -> `ethereum_gold_task`).
4. **Serverless Compute:** Where applicable, Serverless compute will be utilized to reduce cluster boot times from 5 minutes down to 10 seconds.

## Consequences
- **Positive:** Complete elimination of external orchestration infrastructure (no Airflow servers to maintain).
- **Positive:** Deeply integrated observability within the Databricks UI, including matrix views of job runs and native alerting.
- **Negative:** Tightly couples the orchestration logic to the Databricks ecosystem, making cross-platform orchestration (e.g., triggering a non-Databricks GCP Cloud Function as part of the DAG) more difficult compared to a platform-agnostic tool like Airflow.

# ADR-003: Orchestration Strategy

## Status
Accepted

## Context
With our Medallion architecture encompassing ingestion (Bronze), quality checks and cleaning (Silver), and aggregations (Gold), we require a robust orchestration mechanism. The platform relies heavily on Databricks for compute, but we also interact with external services via FastAPI and require a centralized view of our data workflows.

We need to decide whether to use Databricks Workflows exclusively, Airflow exclusively, or a hybrid approach to schedule and manage our ETL pipelines, data quality checks, and maintenance tasks.

## Decision
We will adopt a **Hybrid Orchestration Strategy**:
1. **Airflow (Cloud Composer / Managed Airflow)** will serve as the top-level macro-orchestrator. It will handle cross-platform dependencies (e.g., triggering a Databricks pipeline only after an external GCP process completes).
2. **Databricks Workflows (via Asset Bundles - DABs)** will be used for execution of the actual Spark jobs within Databricks. Airflow will trigger Databricks Workflows via the `DatabricksRunNowOperator` or `DatabricksSubmitRunOperator`.

### Rationale
- **Separation of Concerns:** Airflow handles the "when" and the cross-platform dependencies. Databricks Workflows handle the "how" of Spark execution.
- **Cost Efficiency:** Running spark jobs directly via Databricks Workflows is highly optimized (e.g., Job Clusters). Triggering them from Airflow adds no compute overhead on the Databricks side.
- **GitOps Compatibility:** Databricks Asset Bundles (DABs) allow us to define our Databricks Workflows in YAML (`databricks.yml`) and deploy them natively via CI/CD, which perfectly aligns with our strict GitOps mandate.
- **Extensibility:** If we later need to integrate dbt or an external API into our pipeline, Airflow's vast provider ecosystem makes this trivial.

## Consequences
- **Positive:** We gain a "single pane of glass" in Airflow for all business-level workflows, while leveraging native Databricks optimizations for Spark execution.
- **Positive:** Developer experience is improved through DABs for deployment and Airflow DAGs for macro scheduling.
- **Negative:** Increased complexity due to managing two orchestration tools. Engineers must understand both Airflow DAGs and DABs configurations.
- **Mitigation:** We will strictly enforce that Airflow DAGs only contain lightweight orchestration logic (sensors, operators) and no heavy data transformations. All transformations remain in Databricks/Spark.

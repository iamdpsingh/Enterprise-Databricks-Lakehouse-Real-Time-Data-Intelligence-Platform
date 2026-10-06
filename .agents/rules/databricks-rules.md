# Databricks Platform Rules — Full Specification

## 1. Databricks is the Heart of This Platform
All data processing, transformation, streaming, ML, SQL serving, and data governance happen in Databricks. GCP provides the foundation. Databricks is the engine.

---

## 2. Workspace Architecture

### Environment Topology
| Environment | Workspace | GCP Project | Catalog | Purpose |
|-------------|-----------|-------------|---------|---------|
| Development | `lakehouse-dev` | `project-lakehouse-dev` | `dev_catalog` | Feature development, experimentation |
| Staging | `lakehouse-staging` | `project-lakehouse-stg` | `stg_catalog` | Pre-prod validation, integration tests |
| Production | `lakehouse-prod` | `project-lakehouse-prod` | `prod_catalog` | Live data, business consumers |

### Workspace Configuration
- All workspaces must be deployed in **Secure Cluster Connectivity (No Public IP)** mode.
- Unity Catalog metastore is shared across all workspaces via a single GCP region.
- Git integration must be configured for every workspace pointing to this GitHub repository.

---

## 3. Databricks Asset Bundles (DABs) — Deployment Standard

All Databricks resources (jobs, pipelines, clusters, permissions) must be defined as code using Databricks Asset Bundles. Manual resource creation via the Databricks UI is **forbidden** in Staging and Production.

### Bundle Structure
```
databricks/
├── resources/
│   ├── databricks.yml           # Root bundle config (project name, targets)
│   ├── jobs/
│   │   ├── ingestion_job.yml    # Bronze ingestion job definition
│   │   ├── silver_job.yml       # Silver transformation job
│   │   └── gold_job.yml         # Gold aggregation job
│   ├── pipelines/
│   │   └── streaming_pipeline.yml  # DLT/Lakeflow streaming pipeline
│   └── clusters/
│       └── job_cluster_policy.yml
└── schemas/
    ├── bronze_tables.yml
    └── silver_tables.yml
```

### Root Bundle Config Pattern
```yaml
# databricks/resources/databricks.yml
bundle:
  name: enterprise-lakehouse

variables:
  catalog:
    description: "The Unity Catalog catalog name for this environment"
  environment:
    description: "The deployment environment (dev, staging, prod)"

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: ${workspace.host}  # Set via CI/CD environment variable
    variables:
      catalog: dev_catalog
      environment: dev

  staging:
    mode: staging
    workspace:
      host: ${workspace.host}
    variables:
      catalog: stg_catalog
      environment: staging

  prod:
    mode: production
    workspace:
      host: ${workspace.host}
    variables:
      catalog: prod_catalog
      environment: prod
```

---

## 4. Unity Catalog — Data Architecture

### Catalog-Schema-Table Naming Convention
```
{env}_catalog.{layer}.{domain}_{entity}

Examples:
  prod_catalog.bronze.salesforce_opportunities
  prod_catalog.silver.customers_deduped
  prod_catalog.gold.customer_360
  prod_catalog.quarantine.salesforce_opportunities_quarantine
  prod_catalog.monitoring.data_quality_metrics
```

### External Locations
GCS buckets must be registered as External Locations in Unity Catalog:
```sql
CREATE EXTERNAL LOCATION IF NOT EXISTS raw_data_landing
  URL 'gs://lakehouse-raw-data-prod/landing/'
  WITH (STORAGE CREDENTIAL gcs_service_credential)
  COMMENT 'Landing zone for all raw data from external sources';

CREATE EXTERNAL LOCATION IF NOT EXISTS delta_tables_storage
  URL 'gs://lakehouse-delta-prod/'
  WITH (STORAGE CREDENTIAL gcs_service_credential)
  COMMENT 'Primary storage for all managed Delta tables';
```

---

## 5. Compute Policies & Cluster Configuration

### Job Cluster Defaults (Production)
```yaml
# All production job clusters must use these baseline settings
new_cluster:
  spark_version: "15.4.x-scala2.12"  # LTS version — pin this, update with ADR
  node_type_id: "n2-standard-8"       # GCP instance type
  driver_node_type_id: "n2-standard-4"
  autoscale:
    min_workers: 2
    max_workers: 10
  spark_conf:
    "spark.databricks.delta.preview.enabled": "true"
    "spark.sql.adaptive.enabled": "true"
    "spark.databricks.adaptive.localShuffleReader.enabled": "true"
  custom_tags:
    Project: "enterprise-lakehouse"
    Environment: "${environment}"
    ManagedBy: "databricks-asset-bundles"
```

### Interactive Cluster Policy (Development Only)
```json
{
  "autotermination_minutes": {
    "type": "fixed",
    "value": 45
  },
  "num_workers": {
    "type": "range",
    "maxValue": 4
  },
  "spark_version": {
    "type": "regex",
    "pattern": "^15\\."
  }
}
```

---

## 6. Lakeflow / Delta Live Tables Pipelines

For streaming and complex multi-table pipelines, use Delta Live Tables (Lakeflow).

### DLT Development Rules
- Define streaming tables and materialized views using DLT decorators.
- Use `@dlt.expect()` and `@dlt.expect_or_drop()` for inline data quality expectations.
- Never mix batch and streaming logic in the same DLT pipeline.

### DLT Expectation Pattern
```python
import dlt
from pyspark.sql.functions import col

@dlt.table(
    name="customers_bronze",
    comment="Raw customer records ingested from Salesforce via Auto Loader",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def customers_bronze():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{checkpoint_base}/customers_schema")
        .load(f"gs://{raw_bucket}/salesforce/customers/")
    )


@dlt.table(
    name="customers_silver",
    comment="Cleansed and deduplicated customer records"
)
@dlt.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")
@dlt.expect_or_drop("valid_email", "email RLIKE '^[^@]+@[^@]+\\.[^@]+$'")
@dlt.expect("non_negative_age", "age >= 0")
def customers_silver():
    return (
        dlt.read_stream("customers_bronze")
        .select(
            col("customer_id"),
            col("email"),
            col("age").cast("integer"),
            col("_metadata_ingestion_timestamp")
        )
    )
```

---

## 7. Databricks Workflows — Job Orchestration

### Job Definition Standards
- Every production job must be defined in a YAML file under `databricks/resources/jobs/`.
- Jobs must have `email_notifications` or `webhook_notifications` configured for failures.
- Jobs must have `timeout_seconds` set to prevent runaway jobs.
- Jobs must use `job_clusters` (ephemeral compute), not `existing_cluster_id`.

### Job YAML Template
```yaml
# databricks/resources/jobs/bronze_ingestion_job.yml
resources:
  jobs:
    bronze_ingestion_job:
      name: "[${environment}] Bronze Ingestion — Sales Data"
      description: "Ingests raw sales data from GCS landing zone into Bronze Delta tables"
      timeout_seconds: 3600  # 1 hour max
      max_concurrent_runs: 1
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"  # 2 AM UTC daily
        timezone_id: "UTC"
      email_notifications:
        on_failure:
          - data-engineering@company.com
      tasks:
        - task_key: ingest_sales_bronze
          python_wheel_task:
            package_name: lakehouse
            entry_point: ingest_sales_bronze
            parameters:
              - "--env=${environment}"
              - "--catalog=${catalog}"
          new_cluster:
            spark_version: "15.4.x-scala2.12"
            node_type_id: "n2-standard-8"
            num_workers: 4
```

---

## 8. MLflow — ML Lifecycle

- All ML experiments must be tracked in MLflow with the Databricks managed backend.
- Model registration happens in Unity Catalog via `mlflow.register_model()`.
- Staging models must pass validation before being promoted to `Production` stage.
- Model serving endpoints (Databricks Model Serving) must have authentication enabled.
- Every ML experiment must include: data version/hash used for training, hyperparameters, evaluation metrics, and the model artifact.

---

## 9. Development Workflow in Databricks

### Notebook Development → Production Code Path
1. Start in a Databricks Notebook attached to an interactive cluster (dev workspace only).
2. Validate the logic with sample data.
3. Extract the logic into a Python module in `src/`.
4. Write unit tests in `tests/unit/`.
5. Delete or archive the notebook (it should NOT be the production artifact).
6. Define a Databricks Workflow task to execute the module.
7. Submit PR to `develop`.

### Prohibited in Production
- ❌ Using `dbutils.notebook.run()` as an orchestration mechanism — use Databricks Workflows.
- ❌ Using All-Purpose clusters for scheduled jobs — use Job Clusters.
- ❌ Leaving unused interactive clusters running — set auto-termination.
- ❌ Storing credentials in notebook widgets or cluster environment variables — use Secret Scopes.
- ❌ Mounting GCS buckets via `dbutils.fs.mount()` — use External Locations in Unity Catalog.

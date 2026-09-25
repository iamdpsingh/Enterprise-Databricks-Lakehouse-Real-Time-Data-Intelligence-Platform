# Databricks Rules

## 1. Workspaces and Environments
- **Environment Isolation:** Separate workspaces for Dev, Staging, and Prod.
- **Deployment:** Use Databricks Asset Bundles (DABs) for deploying jobs, pipelines, and ML models.
- **Version Control:** All notebooks and scripts must be stored in the GitHub repository and synced or deployed via DABs. No code should live exclusively in the Databricks workspace UI.

## 2. Unity Catalog
- **Metastore:** A single Unity Catalog metastore per region, shared across workspaces.
- **Catalogs:** Use environment-specific catalogs (e.g., `dev_catalog`, `prod_catalog`).
- **External Locations:** Define external locations for GCS buckets securely using Storage Credentials linked to GCP Service Accounts.
- **Managed vs. External Tables:** Prefer Managed Tables for Delta data unless there is a specific requirement to use External Tables (e.g., integrating with external tools that don't support Unity Catalog).

## 3. Compute and Clusters
- **Job Clusters:** Always use Job Clusters for automated pipelines and workflows. They are cheaper and provide isolated execution environments.
- **All-Purpose Clusters:** Use only for interactive development and ad-hoc analysis. Must have auto-termination enabled (e.g., 60 minutes).
- **Cluster Policies:** Enforce cluster policies to restrict instance types, maximum worker counts, and ensure necessary tags are applied for cost tracking.
- **Photon:** Enable Photon for SQL-heavy workloads or Data Analytics, but evaluate cost-benefit for standard ETL.

## 4. Workflows and Lakeflow
- **Orchestration:** Use Databricks Workflows as the primary orchestrator for tasks within Databricks.
- **Modularity:** Break workflows into smaller, dependent tasks (e.g., Ingestion Task -> Silver Task -> Gold Task) rather than monolithic notebooks.
- **Parameters:** Pass parameters to workflows dynamically via Job parameters or configuration files, not hardcoded in the code.
- **Notifications:** Configure workflow alerts for failures, long-running jobs, and critical successes, routing them to the appropriate channels (e.g., Slack, PagerDuty).

## 5. Development Practices
- **Notebooks vs. Scripts:** Use Notebooks for exploration and visualization. For complex ETL and production pipelines, package code into Python wheels or standard Python modules and execute them as scripts on the cluster.
- **Testing:** Write unit tests for Python modules using `pytest` and execute them in CI before deploying to Databricks.
- **Spark Optimization:**
    - Avoid `collect()` on large datasets.
    - Be mindful of shuffling; use broadcast joins for small tables.
    - Leverage Adaptive Query Execution (AQE).

# Architecture Rules

## System Boundaries
- **GCP** is the cloud foundation: IAM, networking, storage (GCS), Secret Manager, Artifact Registry, Docker compute.
- **Databricks** is the central data platform: all data processing, transformation, streaming, SQL, ML, and governance happen here.
- **GitHub** is the engineering control plane: version control, CI/CD, project management.
- **Next.js** is the operational control center: the monitoring dashboard that gives visibility into the entire platform.
- **Developer Laptop** is for: coding, local unit tests, linting, local documentation, and Git operations only. **No heavy computation runs locally.**

---

## 1. Medallion Architecture — Non-Negotiable Rules

### Bronze Layer
- Bronze is the **raw, unaltered source of truth**. Write-once, append-only.
- Bronze tables must include these metadata columns on every record:
  - `_ingestion_timestamp` — when the record was ingested
  - `_source_file` — source file path or table name
  - `_source_system` — identifier of the source system
  - `_batch_id` — unique batch identifier
  - `_ingestion_id` — unique ingestion run ID
  - `_schema_version` — version of the schema at ingestion time
  - `_processing_status` — `raw` | `quarantined`
  - `_file_modification_time` — timestamp from the source file
  - `_file_size_bytes` — size of the source file at ingestion
- **Never apply business logic in Bronze.**
- **Never run aggregations or joins in Bronze.**
- Raw data must be preserved for **at minimum 1 year** (configurable by data domain).
- Bronze partitioned by ingestion date at minimum.

### Silver Layer
- Silver is the **clean, standardized, deduplicated, and trustworthy** dataset.
- All Silver tables originate from a Bronze source — never from external sources directly.
- Required Silver operations (apply all that are applicable per dataset):
  - Type casting to correct data types
  - Null handling (explicit rules per column — default, drop, or quarantine)
  - Deduplication with documented deduplication key
  - Column standardization (naming conventions, casing)
  - String trimming and encoding normalization
  - Date/timestamp normalization to UTC
  - CDC merge processing (when source is CDC-enabled)
  - Schema enforcement and schema evolution handling
  - Referential integrity checks
  - Application of business rules
  - Records failing validation go to the **Quarantine table** (never silently dropped)
- Silver tables must have column-level comments documenting data type, source, business meaning, and nullable rules.

### Gold Layer
- Gold contains **consumption-ready business data products**.
- Gold is derived exclusively from Silver tables — never from Bronze directly.
- Gold tables are optimized for query performance: `OPTIMIZE`, `ZORDER BY` applied.
- Gold table naming must reflect the business domain: `customer_360`, `daily_revenue`, `fraud_metrics`, `fleet_performance`, `product_performance`, `operational_kpis`.
- Gold tables must be documented with data contracts (`data-contracts/` directory).
- New Gold tables require a PR with ADR justification for the new data product.

---

## 2. Data Quality Architecture

Data quality is a **first-class engineering concern**, not a nice-to-have.

### Mandatory Quality Gates
Every ingestion pipeline must implement quality checks in this order:
1. Schema Validation — structure matches expected schema
2. Type Validation — all columns have correct data types
3. Null Checks — non-nullable columns have no nulls
4. Uniqueness Checks — primary/unique keys have no duplicates
5. Referential Integrity — foreign key references are valid
6. Range Checks — numeric and date values within expected bounds
7. Business Rules — domain-specific rules (e.g., revenue > 0, end_date > start_date)
8. Freshness Check — data is within the expected time window
9. Volume Anomaly Detection — row count within acceptable deviation from historical baseline
10. Duplicate Detection — deduplication key uniqueness enforced

### Quarantine Policy
- Any record failing a quality check at Bronze→Silver transition goes to a quarantine table.
- Quarantine tables follow naming: `{catalog}.quarantine.{source_table}_quarantine`
- Quarantine records must include: original record, failed check name, failure reason, quarantine timestamp.
- Quarantine tables are monitored — alerts fire when quarantine rate exceeds 1% of total records processed.
- Quarantined data must be reviewed within 24 hours of alert.

---

## 3. Data Ingestion Architecture

### Supported Ingestion Patterns
1. **Batch Ingestion** (files from GCS via Auto Loader)
   - Use Databricks Auto Loader with `cloudFiles` format for all file-based ingestion.
   - Auto Loader checkpointing must be persisted in a dedicated GCS path.
   - Supported formats: CSV, JSON, XML, Parquet, Avro, ORC, Delta.

2. **Streaming Ingestion** (real-time event streams)
   - Use Structured Streaming with Databricks.
   - Trigger: `processingTime` or `availableNow` depending on SLA.
   - Watermarking must be applied for late-arriving data.
   - Streaming checkpoints must be persisted in GCS.

3. **CDC (Change Data Capture)**
   - Use Delta CDF (Change Data Feed) for Databricks-to-Databricks CDC.
   - Use MERGE patterns for applying CDC events from external sources.
   - CDC operations: INSERT, UPDATE, DELETE, UPSERT — all must be handled explicitly.

4. **API / Direct Ingestion**
   - Source data from REST APIs using Python ingestion scripts.
   - Rate limiting and retry logic must be implemented.
   - Raw API responses stored in GCS Bronze landing zone before ingestion.

### GCS Landing Zone
- All external data lands in GCS before entering Databricks.
- GCS bucket structure: `gs://{project}-data-{env}/{source_system}/{data_type}/{YYYY}/{MM}/{DD}/`
- Data in the landing zone must be retained before processing for auditing purposes.

---

## 4. Storage Architecture

### Delta Lake Rules
- All Databricks managed tables must use **Delta Lake** format — no Parquet tables without explicit justification in an ADR.
- Enable Delta table statistics collection: `ANALYZE TABLE ... COMPUTE STATISTICS`
- Table maintenance must be scheduled via Databricks Workflows:
  - `OPTIMIZE` on a schedule per table access frequency
  - `VACUUM` with retention period ≥ 7 days (respect `delta.deletedFileRetentionDuration`)
- Delta table properties must be set appropriately:
  - `delta.autoOptimize.optimizeWrite = true`
  - `delta.autoOptimize.autoCompact = true`
  - `delta.enableChangeDataFeed = true` (for tables participating in CDC)
- All tables must be registered in Unity Catalog — no unmanaged tables in ad-hoc paths.

### Unity Catalog Structure
```
catalog_{env}/
├── bronze/        # Raw ingestion tables
├── silver/        # Clean, standardized tables
├── gold/          # Business data products
├── quarantine/    # Failed data quality records
├── ml/            # ML feature tables, model artifacts
└── monitoring/    # System tables, quality metrics
```

---

## 5. Compute Architecture

### Databricks Cluster Policies
- Cluster configurations are defined in version-controlled YAML/JSON files.
- No ad-hoc cluster creation in production without Infrastructure-as-Code.
- Use **Job Compute** (not All-Purpose clusters) for production pipelines.
- Enable **auto-termination** on all interactive clusters (max 60 minutes idle).
- Cluster sizing must be right-sized: start small, scale based on workload metrics.

### Docker Compute (GCP)
- Docker containers run on GCP — never build production Docker images locally.
- Docker images are built in GitHub Actions, scanned, and pushed to GCP Artifact Registry.
- All Dockerfiles must use pinned base image versions (never `:latest`).
- Containers must run as non-root users.
- Docker images must follow multi-stage build patterns to minimize image size.

---

## 6. API Architecture

- All backend APIs must be Python-based (FastAPI recommended).
- APIs must expose Databricks data via SQL Warehouse queries — not direct cluster connections.
- APIs are containerized and deployed on GCP.
- All API endpoints must be versioned: `/api/v1/...`
- API authentication must use service accounts and OAuth2/JWT tokens.
- OpenAPI specification (`openapi.yaml`) must be maintained for all APIs.

---

## 7. Anti-Patterns — Never Do These

- ❌ Never write raw data directly to Silver without going through Bronze.
- ❌ Never silently drop bad records — always route to quarantine.
- ❌ Never use `SELECT *` in production pipelines — explicitly name all columns.
- ❌ Never hardcode environment names, catalog names, bucket names, or credentials.
- ❌ Never use All-Purpose clusters for production job workloads.
- ❌ Never use `:latest` Docker tags in production deployments.
- ❌ Never run heavy computation locally — use GCP/Databricks.
- ❌ Never create unmanaged Delta tables outside of Unity Catalog.
- ❌ Never apply business logic in Bronze.
- ❌ Never derive Gold directly from Bronze.
- ❌ Never VACUUM Delta tables with retention < 7 days.
- ❌ Never commit secrets, credentials, or API keys to Git.
- ❌ Never skip writing a data contract for a new Gold table.

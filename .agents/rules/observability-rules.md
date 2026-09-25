# Observability Rules

## 1. Centralized Telemetry
- All logs, metrics, and traces from GCP, Databricks, and GitHub must be aggregated and accessible from a central location.
- The **Next.js Data Platform Control Center** serves as the primary operational dashboard for stakeholders and engineers.

## 2. Infrastructure Monitoring (GCP)
- **Metrics to Track:** Compute utilization (CPU, memory), storage usage, network I/O, and container health.
- **Alerting:** Set up alerts for critical thresholds (e.g., storage > 85%, memory limits reached, container restarts).

## 3. Data Platform Monitoring (Databricks)
- **Pipeline Health:** Track job execution duration, success/failure rates, retries, and data throughput (records/sec).
- **Streaming Metrics:** Monitor streaming lag (processing time vs. event time) and watermark progression.
- **Cost Monitoring:** Track DBU consumption per pipeline and business unit using tags.

## 4. Data Observability (Quality and Lineage)
- **Freshness:** Alert if critical datasets are not updated within their expected SLAs.
- **Completeness & Volume:** Monitor row counts and track volume anomalies compared to historical baselines.
- **Quality Metrics:** Track the percentage of records failing validation (quarantine rate). Alert if quarantine rate exceeds acceptable thresholds (e.g., > 1%).
- **Schema Drift:** Alert on unexpected schema changes in incoming Bronze data.

## 5. Alerting Strategy
- **Actionable Alerts:** Alerts must require human intervention or investigation. Noise leads to alert fatigue.
- **Severity Levels:**
    - **P1 (Critical):** Production pipeline down, data SLA missed for critical dashboards. Paged immediately.
    - **P2 (High):** Non-critical pipeline failure, elevated quarantine rates. Addressed next business day.
    - **P3 (Warning):** Job duration creeping up, approaching storage limits. Logged as a ticket for review.
- **Runbooks:** Every alert must link to a runbook providing clear investigation and remediation steps.

## 6. Audit Logging
- Ensure audit logging is enabled across all platforms (GCP Cloud Audit Logs, Databricks Audit Logs, Unity Catalog Audit Logs) to track "who did what, when, and where."

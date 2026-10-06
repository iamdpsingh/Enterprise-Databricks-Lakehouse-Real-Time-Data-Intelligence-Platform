# Observability & Monitoring — Full Specification

## 1. The Three Pillars of Observability
The platform implements observability across three layers. Every layer feeds data into the Next.js Data Platform Control Center.

```
┌──────────────────────────────────────────────────┐
│            OBSERVABILITY STACK                   │
│                                                  │
│  Layer 1: Infrastructure (GCP Cloud Operations)  │
│  Layer 2: Data Platform (Databricks System Tables)│
│  Layer 3: Data Quality (Custom Metrics Tables)   │
│                                                  │
│              ↓ All feed into ↓                   │
│                                                  │
│     Next.js Data Platform Control Center         │
└──────────────────────────────────────────────────┘
```

---

## 2. Layer 1 — Infrastructure Monitoring (GCP)

### Metrics to Collect (GCP Cloud Monitoring)
| Metric | Alert Threshold | Severity |
|--------|----------------|----------|
| Cloud Run CPU utilization | > 85% sustained for 5 min | P2 |
| Cloud Run Memory utilization | > 90% | P1 |
| Cloud Run request latency (P95) | > 2000ms | P2 |
| Cloud Run error rate | > 5% | P1 |
| GCS bucket storage | > 80% of quota | P3 |
| GCS request error rate | > 1% | P2 |
| Cloud Logging ingest rate | > 90% of quota | P2 |

### Dashboards Required
- **Infrastructure Overview**: CPU, memory, error rates for all Cloud Run services.
- **Cost Dashboard**: Daily/weekly spend per resource, trend analysis, budget alerts.
- **Network Dashboard**: Egress/ingress traffic, VPC flow logs summary.

---

## 3. Layer 2 — Data Platform Monitoring (Databricks System Tables)

Databricks System Tables provide rich telemetry. Query these via the SQL Warehouse from the Next.js backend.

### Critical Tables to Monitor
```sql
-- Job execution health
SELECT
    job_id,
    run_id,
    job_name,
    result_state,
    start_time,
    end_time,
    DATEDIFF(SECOND, start_time, end_time) AS duration_seconds,
    error_message
FROM system.lakeflow.job_run_timeline
WHERE start_time >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
ORDER BY start_time DESC;

-- Data throughput
SELECT
    table_name,
    operation_metrics.numOutputRows AS rows_written,
    operation_metrics.numFiles AS files_written,
    timestamp
FROM system.storage.table_history
WHERE timestamp >= CURRENT_DATE - INTERVAL 1 DAY;

-- Query performance
SELECT
    statement_id,
    statement_text,
    status,
    duration / 1000.0 AS duration_seconds,
    read_bytes,
    produced_rows
FROM system.query.history
WHERE duration > 30000  -- Queries taking > 30 seconds
ORDER BY duration DESC
LIMIT 50;
```

### Pipeline KPIs Tracked on Dashboard
| KPI | Healthy | Warning | Critical |
|-----|---------|---------|----------|
| Daily job success rate | ≥ 99% | 95–99% | < 95% |
| P95 job duration vs baseline | ≤ 110% | 110–150% | > 150% |
| Streaming lag (P99) | < 60s | 60–300s | > 300s |
| DBU consumption vs budget | ≤ 90% | 90–100% | > 100% |
| Failed jobs (24h) | 0 | 1–3 | > 3 |

---

## 4. Layer 3 — Data Quality Monitoring

Every pipeline must write quality metrics to a centralized monitoring table in Unity Catalog:
`catalog.monitoring.data_quality_metrics`

### Schema of the Quality Metrics Table
```sql
CREATE TABLE IF NOT EXISTS catalog.monitoring.data_quality_metrics (
    pipeline_name        STRING NOT NULL,
    table_name           STRING NOT NULL,
    run_id               STRING NOT NULL,
    run_timestamp        TIMESTAMP NOT NULL,
    check_name           STRING NOT NULL,
    total_records        BIGINT,
    passed_records       BIGINT,
    failed_records       BIGINT,
    quarantine_records   BIGINT,
    pass_rate            DOUBLE,
    is_alertable         BOOLEAN,
    environment          STRING
)
USING DELTA
PARTITIONED BY (DATE(run_timestamp));
```

### Freshness Monitoring
Every Gold table must have a freshness SLA defined. The monitoring system checks it every 15 minutes.

```sql
-- Freshness check for critical Gold tables
SELECT
    table_name,
    MAX(updated_at)                                  AS last_updated,
    DATEDIFF(MINUTE, MAX(updated_at), CURRENT_TIMESTAMP) AS minutes_since_update,
    sla_minutes,
    CASE
        WHEN DATEDIFF(MINUTE, MAX(updated_at), CURRENT_TIMESTAMP) > sla_minutes THEN 'BREACH'
        WHEN DATEDIFF(MINUTE, MAX(updated_at), CURRENT_TIMESTAMP) > sla_minutes * 0.8 THEN 'WARNING'
        ELSE 'OK'
    END AS freshness_status
FROM gold_tables_freshness_config cfg
LEFT JOIN gold_table_watermarks wtm USING (table_name)
GROUP BY table_name, sla_minutes;
```

### Volume Anomaly Detection
Compare today's row count to a rolling 7-day average. Alert if deviation > 30%.

```sql
WITH daily_volumes AS (
    SELECT
        table_name,
        DATE(run_timestamp) AS run_date,
        SUM(total_records)  AS total_records
    FROM catalog.monitoring.data_quality_metrics
    WHERE run_timestamp >= CURRENT_DATE - INTERVAL 8 DAYS
    GROUP BY table_name, DATE(run_timestamp)
),
rolling_avg AS (
    SELECT
        table_name,
        run_date,
        total_records,
        AVG(total_records) OVER (
            PARTITION BY table_name
            ORDER BY run_date
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) AS rolling_7d_avg
    FROM daily_volumes
)
SELECT
    table_name,
    run_date,
    total_records,
    rolling_7d_avg,
    ABS(total_records - rolling_7d_avg) / rolling_7d_avg AS pct_deviation
FROM rolling_avg
WHERE run_date = CURRENT_DATE
  AND ABS(total_records - rolling_7d_avg) / rolling_7d_avg > 0.30;
```

---

## 5. Alerting Architecture

### Alert Severity Definitions
| Level | Definition | Response Time | Channel |
|-------|-----------|--------------|---------|
| P1 Critical | Production pipeline down / data SLA missed | 15 minutes | PagerDuty + Slack #incidents |
| P2 High | Pipeline failed / elevated quarantine rate | 2 hours | Slack #data-engineering-alerts |
| P3 Warning | Performance degradation / approaching limits | Next business day | Slack #data-engineering |
| P4 Info | Job completed / deployment succeeded | N/A | Slack #deployment-notifications |

### Alert Routing Rules
```yaml
# Example alert routing config (alerts/routing.yaml)
routes:
  - match:
      severity: P1
    receiver: pagerduty-critical
    continue: true

  - match:
      severity: P1
    receiver: slack-incidents

  - match:
      severity: P2
    receiver: slack-de-alerts

  - match:
      severity: P3
    receiver: slack-de-general
```

### Runbook Links
Every alert definition must include a `runbook_url` pointing to the relevant runbook in `docs/operations/`:
```yaml
- alert: HighQuarantineRate
  expr: quarantine_rate > 0.01
  labels:
    severity: P2
  annotations:
    summary: "Quarantine rate exceeded 1% for {{ $labels.table_name }}"
    runbook_url: "https://github.com/.../docs/operations/runbook.md#quarantine-rate"
```

---

## 6. Next.js Control Center — Dashboard Routes & Data Sources

| Route | Description | Primary Data Source |
|-------|-------------|-------------------|
| `/overview` | Platform health summary | Databricks System Tables + Quality Metrics |
| `/pipelines` | Job run history and status | `system.lakeflow.job_run_timeline` |
| `/jobs` | Scheduled job definitions and next runs | Databricks Jobs API |
| `/data-quality` | Quality scores per table over time | `monitoring.data_quality_metrics` |
| `/streaming` | Streaming job lag and throughput | `system.lakeflow.*` + Structured Streaming metrics |
| `/tables` | Unity Catalog table inventory and freshness | Unity Catalog API + watermarks |
| `/lineage` | Data lineage graph (Bronze → Gold) | Unity Catalog Lineage API |
| `/alerts` | Active and historical alerts | GCP Monitoring + Databricks alerts |
| `/audit` | Who accessed/modified what data | Unity Catalog Audit Logs |
| `/cost` | DBU consumption and GCP spend | GCP Billing API + Databricks Usage API |
| `/system-health` | Infrastructure health (Cloud Run, GCS) | GCP Cloud Monitoring API |

---

## 7. Schema Drift Detection

Schema drift in Bronze is one of the most common sources of silent data corruption.

### Detection Strategy
1. On every Bronze ingestion run, capture the source schema and compare it against the registered schema in Unity Catalog.
2. Log any new, removed, or type-changed columns as a `SCHEMA_DRIFT` event in the quality metrics table.
3. For Auto Loader, use `cloudFiles.schemaEvolutionMode = "rescue"` to capture unexpected columns into `_rescued_data` without failing the pipeline.
4. Fire a P2 alert whenever schema drift is detected on a critical table.
5. The data engineer must acknowledge the drift, review the change, update the schema documentation, and file an ADR if the change is breaking.

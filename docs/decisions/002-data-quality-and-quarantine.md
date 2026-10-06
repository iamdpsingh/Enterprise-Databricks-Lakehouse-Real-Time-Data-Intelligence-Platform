# ADR-002: Data Quality & Quarantine Strategy

## Status
Accepted

## Context
Data quality is paramount for a Real-Time Data Intelligence Platform. Bad data cascading into the Gold layer invalidates business reporting and ML model predictions. Databricks Delta Live Tables (DLT) provides built-in expectations, but relying solely on them can lead to data loss if invalid records are dropped, or pipeline failure if configured to fail. We need a robust mechanism to validate data, capture invalid records for remediation, and track quality metrics without halting processing for minor issues.

## Decision
We will implement a hybrid Data Quality approach combining native DLT expectations and a custom Quarantine splitting mechanism:

1.  **Rule Definition (`src/quality/rules.py`):**
    *   Quality constraints will be defined in code as reusable Python functions that yield dictionaries.
    *   This ensures rules are testable, version-controlled, and can be dynamically applied.
    *   Every rule will define a specific action (`drop`, `fail`, `quarantine`).

2.  **Quarantine Pattern (`src/quality/quarantine.py`):**
    *   For critical datasets, instead of simply dropping invalid rows, we will use a custom `QuarantineManager`.
    *   This manager evaluates rules against the DataFrame and splits it into two:
        *   `valid_df`: Rows passing all rules. Proceeds to the Silver layer.
        *   `quarantine_df`: Rows failing at least one rule, appended with a `quarantine_reasons` array column.
    *   Quarantined data is routed to a dedicated `_quarantine` table for investigation and replay.

3.  **Metrics Logging (`src/quality/metrics.py`):**
    *   The `QualityMetricsLogger` will parse rule evaluation results and log them to a central Unity Catalog table.
    *   This provides observability into data drift and source system anomalies over time.

## Consequences
**Positive:**
*   **No Data Loss:** Bad records are stored in quarantine, not silently discarded.
*   **Resiliency:** Pipelines don't fail due to isolated bad records, ensuring high availability of the data product.
*   **Observability:** Analysts can track data quality trends via the central metrics table.

**Negative:**
*   **Complexity:** Managing quarantine tables adds storage overhead and requires establishing a process for reviewing and fixing quarantined data (a "Dead Letter Queue" for data).
*   **Performance:** Evaluating rules dynamically and splitting DataFrames introduces slight computational overhead compared to native, unmonitored inserts.

## References
*   Delta Live Tables Expectations Documentation
*   `src/quality/` implementation module

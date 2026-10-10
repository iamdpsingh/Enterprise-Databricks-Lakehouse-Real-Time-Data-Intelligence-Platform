# ADR 002: Data Quality & Quarantine Strategy

## Status
Accepted

## Context
Data ingested from global, uncontrolled sources (like the Ethereum RPC nodes or GitHub Archives) is inherently untrustworthy. Schema drift, malformed JSON structures, and physically impossible values (e.g., geospatial coordinates outside of Earth's bounds) will inevitably occur. If these records enter the Silver or Gold analytical tables, they will corrupt executive dashboards and downstream machine learning models. Standard Spark behavior is to either fail the entire streaming job upon encountering bad data, or silently convert bad fields to NULL. Both are unacceptable for an industrial-scale platform.

## Decision
We will implement a rigorous **Expectations and Quarantine (Dead Letter Queue)** framework between the Bronze and Silver processing layers.

### Implementation Details:
1. **Rule Enforcement:** PySpark logic will explicitly evaluate rows against defined business constraints (e.g. `lat BETWEEN -90 AND 90`).
2. **Fail-Forward Processing:** The streaming job will **never** fail due to data quality issues.
3. **Quarantine Splitting:** Rows that fail critical validations will be split from the main DataFrame.
4. **Metadata Appending:** Failing rows will be appended with a new column `_quarantine_failed_rules` detailing exactly which regex or constraint they failed.
5. **Storage:** Bad rows are flushed into `prod_catalog.quality.quarantine`.

## Consequences
- **Positive:** The Next.js Command Center can directly query the Quarantine table to provide real-time alerts to Data Stewards regarding pipeline health.
- **Positive:** The Silver and Gold tables remain 100% compliant with the Data Contract.
- **Negative:** Requires processing overhead to evaluate rules and split DataFrames. Engineers must remember to regularly query and empty the Quarantine table, or it will bloat indefinitely over time.

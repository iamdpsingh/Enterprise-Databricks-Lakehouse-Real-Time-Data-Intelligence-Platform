# Testing Strategy — Full Specification

## 1. Testing Philosophy
Testing is not an optional step at the end of development. It is a design activity that starts before the first line of production code is written. The test suite is the long-term quality guarantee for this platform.

### Test Pyramid for a Data Platform
```
                      ┌─────────────────┐
                      │  E2E / Pipeline  │  (Few, slow, real data, staging env)
                      └────────┬────────┘
                               │
                     ┌─────────┴─────────┐
                     │  Integration       │  (Some, medium, test cluster)
                     └─────────┬─────────┘
                               │
              ┌────────────────┴────────────────┐
              │         Unit Tests               │  (Many, fast, mocked Spark)
              └─────────────────────────────────┘
```

---

## 2. Unit Testing — The Majority of Tests

### Tools
- `pytest` — test runner.
- `pyspark` in local mode or `pytest-spark` — for testing transformation logic without a cluster.
- `unittest.mock` — for mocking external dependencies.
- `chispa` — for DataFrame equality assertions.

### What Must Be Unit Tested
- Every transformation function in `src/transformations/`.
- Every data quality check in `src/quality/`.
- Every utility function in `src/utilities/`.
- Every ingestion schema validation.

### Pattern — Transformation Unit Test
```python
import pytest
from chispa import assert_df_equality
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

from src.transformations.silver import apply_type_conversions


@pytest.fixture(scope="session")
def spark():
    """Create a local SparkSession for unit testing."""
    return (
        SparkSession.builder
        .master("local[2]")
        .appName("unit-tests")
        .getOrCreate()
    )


def test_apply_type_conversions_casts_timestamp_correctly(spark):
    """Ensure raw timestamp strings are correctly cast to TimestampType."""
    input_data = [("2024-01-15 10:30:00", "100.50")]
    input_df = spark.createDataFrame(input_data, ["event_timestamp_raw", "amount_raw"])

    result_df = apply_type_conversions(input_df)

    assert result_df.schema["event_timestamp"].dataType == TimestampType()
    assert result_df.collect()[0]["event_timestamp"].year == 2024


def test_apply_type_conversions_handles_null_timestamps(spark):
    """Ensure NULL timestamps produce NULL output without crashing."""
    input_data = [(None, "50.00")]
    input_df = spark.createDataFrame(input_data, ["event_timestamp_raw", "amount_raw"])

    result_df = apply_type_conversions(input_df)

    assert result_df.collect()[0]["event_timestamp"] is None
```

### Mocking External Services
```python
from unittest.mock import MagicMock, patch

def test_gcs_reader_handles_missing_file():
    """Ensure ingestion raises DataIngestionError when file not found."""
    with patch("src.ingestion.gcs_reader.storage.Client") as mock_client:
        mock_client.return_value.bucket.return_value.blob.return_value.exists.return_value = False

        with pytest.raises(DataIngestionError, match="Source file not found"):
            read_from_gcs("gs://test-bucket/missing-file.csv")
```

---

## 3. Data Quality Testing

### What Must Be Tested
- Every data quality rule defined in `src/quality/` must have a corresponding test.
- Tests must cover both the PASS case (valid data flows through) and the FAIL case (invalid data is quarantined).

### Pattern — Quality Check Test
```python
def test_null_check_routes_invalid_records_to_quarantine(spark):
    """Records with NULL customer_id must be quarantined, not passed to Silver."""
    input_data = [
        ("C001", "Alice"),   # Valid
        (None, "Bob"),       # Invalid — NULL primary key
        ("C003", "Charlie"), # Valid
    ]
    input_df = spark.createDataFrame(input_data, ["customer_id", "name"])

    valid_df, quarantine_df = apply_null_check(input_df, not_null_columns=["customer_id"])

    assert valid_df.count() == 2
    assert quarantine_df.count() == 1
    assert quarantine_df.collect()[0]["_quarantine_failed_rule"] == "null_check:customer_id"
```

---

## 4. Integration Testing

### What Integration Tests Cover
- Actual read/write operations against the Development Databricks workspace.
- End-to-end Bronze → Silver transformation for a given dataset.
- Databricks Workflow job submission and status checking.
- GCS read/write with actual service account authentication.

### When Integration Tests Run
- **NOT** in CI on every PR (too slow, requires cluster).
- **YES** in the CD pipeline after deployment to Development environment.
- **YES** before promotion from Staging to Production (as a deployment gate).

### Integration Test Isolation
- Always run against a dedicated test catalog in the Dev environment: `dev_catalog.test_<run_id>`.
- Create the test schema at the start of the test session.
- Drop the test schema at the end of the test session (teardown fixture).
- Never run integration tests against the Silver or Gold schemas used by real data.

---

## 5. Pipeline / E2E Testing

### Scope
End-to-end tests validate the full data lifecycle: raw file landing in GCS → Bronze → Silver → Gold.

### Approach
1. Upload a known, synthetic dataset to the GCS landing zone in the Staging environment.
2. Trigger the ingestion Databricks Workflow via the Jobs API.
3. Poll until the job completes.
4. Assert that the expected number of records appear in Bronze, Silver, and Gold tables.
5. Assert that known-bad records appear in the Quarantine table.
6. Assert data quality metrics in the monitoring table.

### Test Data Policy
- All test data must be **synthetic** (generated, not copied from production).
- Test data must cover edge cases: nulls, duplicates, schema drift, out-of-range values.
- A `scripts/generate_test_data.py` script must exist to regenerate test data on demand.

---

## 6. Performance Testing

### What to Benchmark
- Bronze ingestion throughput (records/second) for large files (>1GB).
- Silver transformation duration for standard daily batch sizes.
- Gold table query latency for standard dashboard queries.
- Streaming job latency (event time to Gold availability).

### Performance SLAs (to be defined per pipeline)
| Pipeline | SLA |
|----------|-----|
| Batch Bronze Ingestion | < 30 min for daily load |
| Bronze → Silver (nightly) | < 45 min |
| Gold refresh | < 15 min |
| Streaming lag | < 2 minutes P99 |
| Dashboard query (Gold) | < 5 seconds P95 |

### Regression Detection
- Run performance benchmarks before every Production deployment.
- If a key benchmark degrades by > 20% from the baseline, the deployment must be blocked.

---

## 7. Test Coverage Requirements

| Module | Minimum Coverage |
|--------|-----------------|
| `src/quality/` | 95% |
| `src/transformations/` | 90% |
| `src/ingestion/` | 85% |
| `src/utilities/` | 85% |
| `src/streaming/` | 85% |
| `src/cdc/` | 90% |
| `monitoring-ui/src/` | 80% |

Coverage is checked automatically in CI. PRs that drop coverage below these thresholds are blocked.

---

## 8. Test Naming Conventions

Test files: `test_<module_name>.py`
Test functions: `test_<what_is_tested>_<condition>_<expected_result>()`

Good examples:
- `test_null_validator_with_required_column_missing_raises_quarantine_error()`
- `test_deduplication_with_duplicate_primary_keys_returns_single_record()`
- `test_cdc_merge_with_delete_operation_removes_target_record()`

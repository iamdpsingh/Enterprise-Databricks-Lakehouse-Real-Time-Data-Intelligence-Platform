# Python & PySpark Code Standards (Full Specification)

## 1. Project Setup & Tooling

### pyproject.toml is the Single Configuration File
All Python tooling configuration (dependencies, linting, formatting, type checking, testing) must be defined in `pyproject.toml`. Never use separate `setup.py`, `setup.cfg`, `requirements.txt`, `.flake8`, or `mypy.ini` files.

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "PT", "SIM"]
ignore = ["E501"]  # Line length handled by formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.10"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --cov=src --cov-report=term-missing --cov-fail-under=85"
```

---

## 2. Python Code Style Rules

### Type Hints — Mandatory on All Public Functions
Every function and method that is part of the public API of any module must have full type annotations.
```python
# BAD
def process_records(records, config):
    pass

# GOOD
from typing import Any
def process_records(records: list[dict[str, Any]], config: dict[str, str]) -> int:
    """Process ingested records and return count of successfully processed rows."""
    pass
```

### Docstrings — Google Style on Every Class and Public Method
```python
def validate_schema(df: DataFrame, expected_schema: StructType) -> ValidationResult:
    """Validates a DataFrame against the expected Delta table schema.

    Args:
        df: The input Spark DataFrame to validate.
        expected_schema: The expected StructType schema.

    Returns:
        A ValidationResult containing pass/fail status and field-level errors.

    Raises:
        SchemaValidationError: If the DataFrame is empty or schema is None.
    """
```

### Module Organization
Every Python module must have this structure:
1. Module-level docstring.
2. Standard library imports.
3. Third-party imports (pyspark, delta, etc.).
4. Local imports (from `src.*`).
5. Module-level constants (UPPERCASE).
6. Classes.
7. Functions.
8. `if __name__ == "__main__":` block (only for entry points).

### Constants vs Magic Numbers
```python
# BAD
if quarantine_rate > 0.01:
    trigger_alert()

# GOOD
MAX_QUARANTINE_RATE_THRESHOLD = 0.01

if quarantine_rate > MAX_QUARANTINE_RATE_THRESHOLD:
    trigger_alert()
```

### Exception Handling
- Never use bare `except:` clauses.
- Always catch specific exception types.
- Always log the exception before re-raising or handling it.
- Never silently swallow exceptions in production code.

```python
# BAD
try:
    df = spark.read.parquet(path)
except:
    pass

# GOOD
from src.utilities.logging import get_logger
logger = get_logger(__name__)

try:
    df = spark.read.parquet(path)
except AnalysisException as e:
    logger.error("Failed to read Parquet file at %s: %s", path, str(e))
    raise DataIngestionError(f"Cannot read source file: {path}") from e
```

---

## 3. PySpark-Specific Rules

### Explicit Column Selection — No `SELECT *`
```python
# BAD
df_silver = df_bronze.select("*")

# GOOD
df_silver = df_bronze.select(
    col("customer_id"),
    col("transaction_date").cast(TimestampType()).alias("transaction_timestamp_utc"),
    col("amount").cast(DecimalType(18, 2)).alias("transaction_amount"),
    col("_metadata_batch_id"),
)
```

### Avoid `.collect()` and `.toPandas()` on Large DataFrames
These operations bring data to the driver and will cause OOM errors at scale.
- `.collect()` is acceptable ONLY on aggregated results with a known small row count (e.g., `< 1000 rows`).
- `.toPandas()` is acceptable ONLY in Gold summary queries for dashboard metrics.
- Add a comment whenever you use either, justifying the row count bound.

### Column Naming Convention
- All column names: `snake_case`.
- All internal metadata columns: `_metadata_*` prefix.
- All quarantine metadata columns: `_quarantine_*` prefix.
- No spaces, hyphens, or special characters in column names.

### Transformation Function Signature Pattern
Every transformation function must accept a `DataFrame` and return a `DataFrame`. This ensures composability and testability.

```python
def apply_type_conversions(df: DataFrame) -> DataFrame:
    """Cast Bronze raw strings to Silver typed columns."""
    return df.withColumn(
        "event_timestamp",
        to_timestamp(col("event_timestamp_raw"), "yyyy-MM-dd HH:mm:ss")
    ).withColumn(
        "amount",
        col("amount_raw").cast(DecimalType(18, 4))
    )
```

### Broadcast Joins
Always use broadcast hints for joins where one DataFrame is small (< 100MB) to avoid expensive shuffles:
```python
from pyspark.sql.functions import broadcast

df_result = df_large.join(broadcast(df_small_lookup), on="customer_id", how="left")
```

### Partitioning on Write
Always partition large Delta tables by date on write for performance:
```python
df.write.format("delta") \
    .mode("append") \
    .partitionBy("ingestion_date") \
    .option("mergeSchema", "true") \
    .saveAsTable("catalog.bronze.sales_transactions")
```

---

## 4. SQL Standards

### Formatting (enforced by sqlfluff)
- SQL keywords: UPPERCASE (`SELECT`, `FROM`, `WHERE`, `JOIN`, `GROUP BY`).
- Table and column names: `snake_case`.
- Always use explicit aliases for calculated columns.
- Maximum line length: 100 characters.
- Use CTEs (WITH clauses) instead of nested subqueries.

```sql
-- BAD
select customer_id, sum(amount) from transactions where dt >= '2024-01-01' group by 1;

-- GOOD
WITH daily_transactions AS (
    SELECT
        customer_id,
        transaction_date,
        SUM(amount)          AS total_amount,
        COUNT(transaction_id) AS transaction_count
    FROM silver.transactions
    WHERE transaction_date >= '2024-01-01'
    GROUP BY
        customer_id,
        transaction_date
)

SELECT * FROM daily_transactions;
```

### MERGE Pattern for CDC
```sql
MERGE INTO silver.customers AS target
USING (
    SELECT *
    FROM bronze.customers_cdc
    WHERE _metadata_batch_id = :batch_id
) AS source
ON target.customer_id = source.customer_id
WHEN MATCHED AND source.operation = 'UPDATE' THEN
    UPDATE SET *
WHEN MATCHED AND source.operation = 'DELETE' THEN
    DELETE
WHEN NOT MATCHED AND source.operation IN ('INSERT', 'UPSERT') THEN
    INSERT *;
```

---

## 5. Configuration-Driven Design

Never hardcode environment names, catalog names, schema names, bucket paths, or cluster IDs in code. All configurable values must be loaded from a config object.

```python
# BAD
catalog = "prod_catalog"
schema = "silver"
table = f"{catalog}.{schema}.customers"

# GOOD
from src.utilities.config import PipelineConfig

config = PipelineConfig.load(env=spark.conf.get("pipeline.environment"))
table = f"{config.catalog}.{config.silver_schema}.customers"
```

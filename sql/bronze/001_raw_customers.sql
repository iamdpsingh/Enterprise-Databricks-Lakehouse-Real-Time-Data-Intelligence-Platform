-- ==============================================================================
-- Bronze Layer: Raw Customers
-- Purpose: Append-only raw ingestion from source systems.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS main.bronze.raw_customers (
    -- Source Data Columns (Schemaless / Variant for flexibility)
    payload STRING COMMENT 'Raw JSON payload from source API',
    
    -- Audit Metadata (Injected by src/ingestion/metadata.py)
    _bronze_ingested_at TIMESTAMP COMMENT 'Timestamp of insertion into Bronze',
    _bronze_file_name STRING COMMENT 'Source file path or API endpoint',
    _bronze_rescued_data STRING COMMENT 'Rescued data from Auto Loader'
)
USING DELTA
TBLPROPERTIES (
    'delta.appendOnly' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Raw append-only customer data ingested from external APIs.';

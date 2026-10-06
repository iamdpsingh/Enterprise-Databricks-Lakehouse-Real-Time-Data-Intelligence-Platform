-- ==============================================================================
-- Silver Layer: Cleaned Customers (SCD Type 2)
-- Purpose: Deduplicated, cleaned, and standardized customer entity records.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS main.silver.customers (
    -- Business Keys & Attributes
    customer_id STRING NOT NULL COMMENT 'Unique identifier from source system',
    first_name STRING COMMENT 'Customer first name (trimmed)',
    last_name STRING COMMENT 'Customer last name (trimmed)',
    email STRING COMMENT 'Pseudonymized email address',
    created_at TIMESTAMP COMMENT 'Record creation time in source',
    updated_at TIMESTAMP COMMENT 'Record update time in source',
    
    -- SCD2 Metadata
    is_current BOOLEAN NOT NULL COMMENT 'True if this is the active record',
    valid_from TIMESTAMP NOT NULL COMMENT 'SCD2 Valid From timestamp',
    valid_to TIMESTAMP COMMENT 'SCD2 Valid To timestamp (Null if active)',
    
    -- Data Quality Metadata
    _quarantine_reasons ARRAY<STRING> COMMENT 'Reasons for quarantine (if any)'
)
USING DELTA
PARTITIONED BY (is_current)
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Cleaned, SCD2 dimension table for Customer entities.';

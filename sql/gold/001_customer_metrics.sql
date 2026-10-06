-- ==============================================================================
-- Gold Layer: Customer Activity Metrics
-- Purpose: Aggregated, business-level metrics for reporting and dashboards.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS main.gold.customer_metrics (
    -- Dimension Keys
    customer_id STRING NOT NULL COMMENT 'Foreign key to silver.customers',
    
    -- Aggregated Metrics
    total_lifetime_value DECIMAL(18, 2) DEFAULT 0.00 COMMENT 'Total LTV in USD',
    total_orders INT DEFAULT 0 COMMENT 'Count of completed orders',
    first_order_date DATE COMMENT 'Date of first order',
    last_order_date DATE COMMENT 'Date of most recent order',
    
    -- Audit Metadata
    _gold_updated_at TIMESTAMP NOT NULL COMMENT 'Timestamp when this metric was last calculated'
)
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Aggregated KPIs and metrics for customers.';

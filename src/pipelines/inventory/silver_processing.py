from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from delta.tables import DeltaTable

from src.cdc.scd2 import merge_scd2
from src.transformations.cleaning import standardize_nulls
from src.quality.quarantine import apply_quality_rules, write_to_quarantine
from src.quality.rules import QualityRule, rule_is_not_null
from src.utilities.logger import logger

def process_inventory_silver(spark: SparkSession, bronze_table: str, silver_table: str, quarantine_table: str) -> None:
    """
    Reads inventory updates from Bronze, cleans, validates, and applies an SCD Type 2 
    upsert into the Silver table (tracking historical stock levels).
    """
    logger.info(f"Starting Silver processing for Inventory. Reading from {bronze_table}")
    
    raw_df = spark.read.table(bronze_table)
    cleaned_df = standardize_nulls(raw_df)
    
    # Data Quality Checks: product_id must exist, stock >= 0
    rules = [
        rule_is_not_null("product_id"),
        rule_is_not_null("warehouse_id"),
        QualityRule(
            name="stock_level_non_negative",
            description="Ensure stock level is not negative",
            expression=F.col("stock_level") >= 0
        )
    ]
    
    valid_df, quarantine_df = apply_quality_rules(cleaned_df, rules, quarantine_reason_col="quarantine_reason")
    
    # Handle Quarantine
    if quarantine_df.count() > 0:
        logger.warning(f"Routing {quarantine_df.count()} invalid inventory records to {quarantine_table}")
        write_to_quarantine(quarantine_df, quarantine_table)
        
    # Apply SCD Type 2 to Silver to track historical stock changes
    if valid_df.count() > 0:
        logger.info(f"Applying SCD2 upsert for {valid_df.count()} valid records to {silver_table}")
        silver_dt = DeltaTable.forName(spark, silver_table)
        
        merge_scd2(
            target_table=silver_dt,
            source_df=valid_df,
            primary_keys=["product_id", "warehouse_id"],
            update_timestamp_col="updated_at"
        )
    
    logger.info("Silver processing for Inventory completed successfully.")

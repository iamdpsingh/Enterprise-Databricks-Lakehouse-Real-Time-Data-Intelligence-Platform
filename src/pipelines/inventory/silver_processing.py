from pyspark.sql import SparkSession
from delta.tables import DeltaTable

from src.cdc.scd2 import upsert_scd2
from src.transformations.cleaning import standardize_nulls
from src.quality.quarantine import QuarantineManager
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
        "product_id IS NOT NULL",
        "stock_level >= 0",
        "warehouse_id IS NOT NULL"
    ]
    
    valid_df, quarantine_df = QuarantineManager.split_valid_invalid(cleaned_df, rules)
    
    # Handle Quarantine
    if quarantine_df.count() > 0:
        logger.warning(f"Routing {quarantine_df.count()} invalid inventory records to {quarantine_table}")
        quarantine_df.write.format("delta").mode("append").saveAsTable(quarantine_table)
        
    # Apply SCD Type 2 to Silver to track historical stock changes
    if valid_df.count() > 0:
        logger.info(f"Applying SCD2 upsert for {valid_df.count()} valid records to {silver_table}")
        silver_dt = DeltaTable.forName(spark, silver_table)
        
        upsert_scd2(
            target_table=silver_dt,
            source_df=valid_df,
            primary_keys=["product_id", "warehouse_id"],
            order_by_col="updated_at"
        )
    
    logger.info("Silver processing for Inventory completed successfully.")

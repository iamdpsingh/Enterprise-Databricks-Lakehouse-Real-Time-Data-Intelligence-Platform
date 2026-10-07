from pyspark.sql import SparkSession
from delta.tables import DeltaTable

from src.cdc.scd1 import upsert_scd1
from src.transformations.cleaning import cast_column, standardize_nulls
from src.quality.quarantine import QuarantineManager
from src.quality.rules import expect_column_to_not_be_null
from src.utilities.logger import logger

def process_orders_silver(spark: SparkSession, bronze_table: str, silver_table: str, quarantine_table: str) -> None:
    """
    Reads new orders from Bronze, cleans the data, runs quality checks,
    quarantines bad records, and upserts (SCD1) valid records into Silver.
    """
    logger.info(f"Starting Silver processing for Orders. Reading from {bronze_table}")
    
    # 1. Read from Bronze
    raw_df = spark.read.table(bronze_table)
    
    # 2. Clean & Standardize
    # Assume payload contains JSON that we parse (simplified here)
    cleaned_df = standardize_nulls(raw_df)
    
    # 3. Data Quality Checks (Quarantine Pattern)
    # We require order_id and customer_id to be not null
    rules = [
        "order_id IS NOT NULL",
        "customer_id IS NOT NULL",
        "total_amount >= 0"
    ]
    
    valid_df, quarantine_df = QuarantineManager.split_valid_invalid(cleaned_df, rules)
    
    # 4. Handle Quarantine
    if quarantine_df.count() > 0:
        logger.warning(f"Found {quarantine_df.count()} invalid order records. Routing to {quarantine_table}")
        quarantine_df.write.format("delta").mode("append").saveAsTable(quarantine_table)
        
    # 5. Upsert Valid Records to Silver (SCD1)
    if valid_df.count() > 0:
        logger.info(f"Upserting {valid_df.count()} valid records to {silver_table}")
        silver_dt = DeltaTable.forName(spark, silver_table)
        
        upsert_scd1(
            target_table=silver_dt,
            source_df=valid_df,
            primary_keys=["order_id"]
        )
    
    logger.info("Silver processing for Orders completed successfully.")

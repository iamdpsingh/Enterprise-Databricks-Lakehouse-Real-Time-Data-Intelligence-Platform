from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.utilities.logger import logger

def aggregate_inventory_gold(spark: SparkSession, silver_table: str, gold_table: str) -> None:
    """
    Reads active inventory records from Silver (SCD2) and calculates 
    real-time aggregated stock metrics per warehouse.
    """
    logger.info(f"Starting Gold aggregation for Inventory. Reading from {silver_table}")
    
    silver_df = spark.read.table(silver_table)
    
    # Filter only currently active records from SCD2
    active_inventory = silver_df.filter(F.col("is_current") == True)
    
    # Aggregate stock by warehouse
    gold_df = (
        active_inventory
        .groupBy("warehouse_id")
        .agg(
            F.sum("stock_level").alias("total_stock_level"),
            F.count("product_id").alias("unique_products_in_stock")
        )
        .withColumn("_gold_updated_at", F.current_timestamp())
    )
    
    logger.info(f"Writing aggregated inventory data to {gold_table}")
    gold_df.write.format("delta").mode("overwrite").saveAsTable(gold_table)
    
    logger.info("Gold aggregation for Inventory completed successfully.")

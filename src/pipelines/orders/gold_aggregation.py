from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.utilities.logger import logger

def aggregate_orders_gold(spark: SparkSession, silver_table: str, gold_table: str) -> None:
    """
    Reads cleaned orders from Silver, aggregates them to create a daily 
    summary of total revenue and order counts, and writes to Gold.
    """
    logger.info(f"Starting Gold aggregation for Orders. Reading from {silver_table}")
    
    silver_df = spark.read.table(silver_table)
    
    # Aggregate by date
    gold_df = (
        silver_df
        .withColumn("order_date", F.to_date(F.col("created_at")))
        .groupBy("order_date")
        .agg(
            F.sum("total_amount").alias("daily_revenue"),
            F.count("order_id").alias("daily_order_count"),
            F.countDistinct("customer_id").alias("unique_customers")
        )
        .withColumn("_gold_updated_at", F.current_timestamp())
    )
    
    logger.info(f"Writing aggregated data to {gold_table}")
    
    # Overwrite the Gold table (or merge depending on requirements, here we do a simple overwrite for the aggregate)
    gold_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(gold_table)
    
    logger.info("Gold aggregation for Orders completed successfully.")

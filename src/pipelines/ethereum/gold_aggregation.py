from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.utilities.logger import logger

def process_gold(spark: SparkSession, silver_table: str, gold_table: str):
    """Ethereum Web3 Gold layer."""
    logger.info("Starting Ethereum Gold aggregation")
    try:
        df = spark.read.table(silver_table)
    except Exception:
        return
        
    agg_df = (
        df.withColumn("block_date", F.to_date(F.col("block_timestamp")))
        .groupBy("block_date", "to_address")
        .agg(
            F.sum("value_long").alias("total_eth_transferred"),
            F.avg("gas_long").alias("avg_gas_used"),
            F.count("hash").alias("tx_count")
        )
    )
    
    agg_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(gold_table)

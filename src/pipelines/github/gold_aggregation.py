from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.utilities.logger import logger

def process_gold(spark: SparkSession, silver_table: str, gold_table: str):
    logger.info("Starting GitHub Archive Gold aggregation")
    try:
        df = spark.read.table(silver_table)
    except Exception:
        return
        
    agg_df = (
        df.withColumn("event_date", F.to_date(F.col("created_at")))
        .groupBy("repo_name", "event_date", "type")
        .agg(F.count("id").alias("event_count"))
    )
    
    agg_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(gold_table)

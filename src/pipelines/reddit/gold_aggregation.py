from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.utilities.logger import logger

def process_gold(spark: SparkSession, silver_table: str, gold_table: str):
    """
    Gold processing for Reddit Pushshift.
    Aggregates daily topic volume and basic metrics on active records.
    """
    logger.info(f"Starting Reddit Gold aggregation from {silver_table} to {gold_table}")
    
    try:
        df = spark.read.table(silver_table).where("is_current = true")
    except Exception:
        logger.error(f"Silver table {silver_table} not found.")
        return
        
    agg_df = (
        df.withColumn("post_date", F.to_date(F.from_unixtime(F.col("created_utc"))))
        .groupBy("subreddit", "post_date")
        .agg(
            F.count("id").alias("total_posts"),
            F.avg("score").alias("avg_score"),
            F.sum("num_comments").alias("total_comments")
        )
    )
    
    agg_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(gold_table)

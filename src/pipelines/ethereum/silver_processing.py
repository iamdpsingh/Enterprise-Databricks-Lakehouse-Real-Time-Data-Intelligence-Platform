from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.quality.rules import rule_is_not_null
from src.quality.quarantine import apply_quality_rules, write_to_quarantine
from src.utilities.logger import logger

def process_silver(spark: SparkSession, bronze_table: str, silver_table: str, quarantine_table: str):
    """Ethereum Web3 Silver layer."""
    logger.info("Starting Ethereum Silver processing")
    try:
        df = spark.read.table(bronze_table)
    except Exception:
        return
    
    # Cast complex hex strings to long
    df = df.withColumn("gas_long", F.conv(F.substring(F.col("gas"), 3, 100), 16, 10).cast("long"))
    df = df.withColumn("value_long", F.conv(F.substring(F.col("value"), 3, 100), 16, 10).cast("long"))
    
    rules = [rule_is_not_null("hash", is_fatal=True)]
    valid_df, quarantine_df = apply_quality_rules(df, rules)
    write_to_quarantine(quarantine_df, quarantine_table)
    
    valid_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(silver_table)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.quality.rules import rule_is_not_null, QualityRule
from src.quality.quarantine import apply_quality_rules, write_to_quarantine
from src.utilities.logger import logger

def process_silver(spark: SparkSession, bronze_table: str, silver_table: str, quarantine_table: str):
    logger.info("Starting Overture Maps Silver processing")
    try:
        df = spark.read.table(bronze_table)
    except Exception:
        return
        
    # Geospatial cleaning: filter out invalid coordinates
    rules = [
        rule_is_not_null("id", is_fatal=True),
        QualityRule(
            name="valid_coords",
            description="Latitude between -90/90, Longitude between -180/180",
            expression=(F.col("lat") >= -90) & (F.col("lat") <= 90) & (F.col("lon") >= -180) & (F.col("lon") <= 180),
            is_fatal=True
        )
    ]
    valid_df, quarantine_df = apply_quality_rules(df, rules)
    write_to_quarantine(quarantine_df, quarantine_table)
    
    valid_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(silver_table)

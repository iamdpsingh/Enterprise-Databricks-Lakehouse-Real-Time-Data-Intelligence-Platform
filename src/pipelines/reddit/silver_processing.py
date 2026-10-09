from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from delta.tables import DeltaTable

from src.quality.rules import rule_is_not_null
from src.quality.quarantine import apply_quality_rules, write_to_quarantine
from src.transformations.pii_masking import pseudonymize_email
from src.cdc.scd2 import merge_scd2
from src.utilities.logger import logger

def process_silver(spark: SparkSession, bronze_table: str, silver_table: str, quarantine_table: str):
    """
    Silver processing for Reddit Pushshift.
    Applies data quality rules, PII masking, and SCD Type 2 CDC.
    """
    logger.info(f"Starting Reddit Silver processing from {bronze_table} to {silver_table}")
    
    # 1. Read Bronze data
    try:
        df = spark.read.table(bronze_table)
    except Exception as e:
        logger.error(f"Bronze table {bronze_table} not found.")
        return
    
    # 2. Apply transformations (Text cleaning & PII masking)
    df = df.withColumn(
        "clean_text", 
        F.regexp_replace(F.col("selftext"), r"<[^>]+>", "") # Clean HTML
    )
    # Mask author emails if they inadvertently put them in
    df = pseudonymize_email(df, "author")
    
    # 3. Data Quality Rules
    rules = [
        rule_is_not_null("id", is_fatal=True),
        rule_is_not_null("author", is_fatal=True)
    ]
    valid_df, quarantine_df = apply_quality_rules(df, rules)
    
    # 4. Write Quarantined records
    write_to_quarantine(quarantine_df, quarantine_table)
    
    # 5. SCD2 Merge into Silver
    try:
        target_delta = DeltaTable.forName(spark, silver_table)
        valid_df = valid_df.withColumn("updated_at", F.current_timestamp())
        merge_scd2(
            target_table=target_delta,
            source_df=valid_df,
            primary_keys=["id"],
            update_timestamp_col="updated_at"
        )
    except Exception:
        logger.info(f"Initializing Silver table {silver_table}")
        init_df = valid_df.withColumn("updated_at", F.current_timestamp()) \
                          .withColumn("is_current", F.lit(True)) \
                          .withColumn("valid_from", F.current_timestamp()) \
                          .withColumn("valid_to", F.lit(None).cast("timestamp"))
        init_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.quality.rules import rule_is_not_null
from src.quality.quarantine import apply_quality_rules, write_to_quarantine
from src.utilities.logger import logger

def process_silver(spark: SparkSession, bronze_table: str, silver_table: str, quarantine_table: str):
    logger.info("Starting GitHub Archive Silver processing")
    try:
        df = spark.read.table(bronze_table)
    except Exception:
        return
        
    # Deduplicate nested event payloads
    df = df.dropDuplicates(["id"])
    
    # Extract repo name from nested struct (handle string if it wasn't parsed as struct yet)
    # Using generic cast since schema evolution might leave it as string initially
    df = df.withColumn("repo_name", F.col("repo").getItem("name") if dict(df.dtypes).get('repo', '').startswith('struct') else F.col("repo"))
    
    rules = [rule_is_not_null("id", is_fatal=True)]
    valid_df, quarantine_df = apply_quality_rules(df, rules)
    write_to_quarantine(quarantine_df, quarantine_table)
    
    valid_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(silver_table)

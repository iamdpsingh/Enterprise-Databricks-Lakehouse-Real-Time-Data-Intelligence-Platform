import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

def test_github_silver(spark: SparkSession, tmp_path):
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("repo", StringType(), True),
        StructField("type", StringType(), True)
    ])
    df = spark.createDataFrame([
        ("event1", "repo_a", "PushEvent"), 
        ("event1", "repo_a", "PushEvent"), # Duplicate
        (None, "repo_b", "PullRequestEvent") 
    ], schema)
    
    df.write.format("delta").save(f"{tmp_path}/bronze_github")
    spark.sql(f"CREATE TABLE bronze_github USING DELTA LOCATION '{tmp_path}/bronze_github'")
    
    from src.pipelines.github.silver_processing import process_silver
    process_silver(spark, "bronze_github", "silver_github", "quarantine_github")
    
    try:
        silver_df = spark.read.table("silver_github")
        assert silver_df.count() == 1 # Deduplicated and valid
        
        quarantine_df = spark.read.table("quarantine_github")
        assert quarantine_df.count() == 1 # Null ID
    finally:
        spark.sql("DROP TABLE IF EXISTS bronze_github")
        spark.sql("DROP TABLE IF EXISTS silver_github")
        spark.sql("DROP TABLE IF EXISTS quarantine_github")

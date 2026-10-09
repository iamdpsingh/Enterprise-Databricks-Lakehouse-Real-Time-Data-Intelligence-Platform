import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, LongType

def test_reddit_silver(spark: SparkSession, tmp_path):
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("author", StringType(), True),
        StructField("selftext", StringType(), True),
        StructField("created_utc", LongType(), True)
    ])
    df = spark.createDataFrame([
        ("123", "user1@email.com", "<p>Hello</p>", 1600000000), 
        (None, "user2", "World", 1600000000)
    ], schema)
    
    df.write.format("delta").save(f"{tmp_path}/bronze_reddit")
    spark.sql(f"CREATE TABLE bronze_reddit USING DELTA LOCATION '{tmp_path}/bronze_reddit'")
    
    from src.pipelines.reddit.silver_processing import process_silver
    process_silver(spark, "bronze_reddit", "silver_reddit", "quarantine_reddit")
    
    try:
        silver_df = spark.read.table("silver_reddit")
        assert silver_df.count() == 1
        row = silver_df.first()
        assert row["clean_text"] == "Hello"
        assert row["author"] == "u***@email.com" # Masked
        
        quarantine_df = spark.read.table("quarantine_reddit")
        assert quarantine_df.count() == 1
    finally:
        spark.sql("DROP TABLE IF EXISTS bronze_reddit")
        spark.sql("DROP TABLE IF EXISTS silver_reddit")
        spark.sql("DROP TABLE IF EXISTS quarantine_reddit")

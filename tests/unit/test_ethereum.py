import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

def test_ethereum_silver(spark: SparkSession, tmp_path):
    # Setup test data
    schema = StructType([
        StructField("hash", StringType(), True),
        StructField("gas", StringType(), True),
        StructField("value", StringType(), True)
    ])
    df = spark.createDataFrame([
        ("0xabc", "0x5208", "0x0"),  # Valid, gas=21000
        (None, "0x5208", "0x0")      # Invalid hash
    ], schema)
    
    df.write.format("delta").save(f"{tmp_path}/bronze_eth")
    spark.sql(f"CREATE TABLE bronze_eth USING DELTA LOCATION '{tmp_path}/bronze_eth'")
    
    from src.pipelines.ethereum.silver_processing import process_silver
    process_silver(spark, "bronze_eth", "silver_eth", "quarantine_eth")
    
    # Assertions
    try:
        silver_df = spark.read.table("silver_eth")
        assert silver_df.count() == 1
        assert silver_df.first()["gas_long"] == 21000
        
        quarantine_df = spark.read.table("quarantine_eth")
        assert quarantine_df.count() == 1
    finally:
        spark.sql("DROP TABLE IF EXISTS bronze_eth")
        spark.sql("DROP TABLE IF EXISTS silver_eth")
        spark.sql("DROP TABLE IF EXISTS quarantine_eth")

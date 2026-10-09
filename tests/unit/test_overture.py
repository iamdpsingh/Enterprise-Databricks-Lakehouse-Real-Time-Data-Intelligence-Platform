import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

def test_overture_silver(spark: SparkSession, tmp_path):
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("lat", DoubleType(), True),
        StructField("lon", DoubleType(), True)
    ])
    df = spark.createDataFrame([
        ("poi1", 45.0, 90.0),   # Valid
        ("poi2", 100.0, 90.0)   # Invalid lat
    ], schema)
    
    df.write.format("delta").save(f"{tmp_path}/bronze_overture")
    spark.sql(f"CREATE TABLE bronze_overture USING DELTA LOCATION '{tmp_path}/bronze_overture'")
    
    from src.pipelines.overture.silver_processing import process_silver
    process_silver(spark, "bronze_overture", "silver_overture", "quarantine_overture")
    
    try:
        silver_df = spark.read.table("silver_overture")
        assert silver_df.count() == 1
        
        quarantine_df = spark.read.table("quarantine_overture")
        assert quarantine_df.count() == 1
        assert "valid_coords" in quarantine_df.first()["_quarantine_failed_rules"]
    finally:
        spark.sql("DROP TABLE IF EXISTS bronze_overture")
        spark.sql("DROP TABLE IF EXISTS silver_overture")
        spark.sql("DROP TABLE IF EXISTS quarantine_overture")

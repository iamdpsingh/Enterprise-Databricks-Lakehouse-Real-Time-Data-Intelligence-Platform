import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType

from src.pipelines.trips.silver_processing import process_trips_silver

@pytest.fixture
def trips_bronze_schema():
    return StructType([
        StructField("vendor_id", StringType(), True),
        StructField("pickup_datetime", TimestampType(), True),
        StructField("dropoff_datetime", TimestampType(), True),
        StructField("passenger_count", IntegerType(), True),
        StructField("trip_distance", DoubleType(), True),
        StructField("fare_amount", DoubleType(), True),
        StructField("_ingested_at", TimestampType(), True)
    ])

def test_process_trips_silver_quarantine(spark: SparkSession, tmp_path, trips_bronze_schema):
    """
    Test that invalid trip records (negative fare, zero passengers, missing IDs) are quarantined.
    """
    bronze_path = f"{tmp_path}/bronze"
    silver_path = f"{tmp_path}/silver"
    quarantine_path = f"{tmp_path}/quarantine"
    checkpoints_path = f"{tmp_path}/checkpoints"
    
    # Create sample bronze data
    from datetime import datetime
    dt = datetime(2015, 10, 1, 12, 0, 0)
    bronze_data = [
        ("V1", dt, dt, 1, 2.5, 10.0, dt),     # Valid
        (None, dt, dt, 1, 2.5, 10.0, dt),     # Invalid: missing vendor_id
        ("V2", dt, dt, 0, 2.5, 10.0, dt),     # Invalid: passenger_count = 0
        ("V3", dt, dt, 1, 2.5, -5.0, dt)      # Invalid: negative fare
    ]
    
    bronze_df = spark.createDataFrame(bronze_data, trips_bronze_schema)
    bronze_df.write.format("delta").save(bronze_path)
    
    spark.sql("DROP TABLE IF EXISTS bronze_trips")
    spark.sql(f"CREATE TABLE bronze_trips USING DELTA LOCATION '{bronze_path}'")
    
    # Create empty external tables so toTable writes to tmp_path instead of spark-warehouse
    spark.sql("DROP TABLE IF EXISTS silver_trips")
    spark.sql("DROP TABLE IF EXISTS quarantine_trips")
    
    # We use the bronze schema to initialize the tables, and rely on mergeSchema="true" 
    # in the pipeline to add _processed_at and _quarantine_failed_rules automatically
    spark.createDataFrame([], trips_bronze_schema).write.format("delta").mode("overwrite").save(silver_path)
    spark.sql(f"CREATE TABLE silver_trips USING DELTA LOCATION '{silver_path}'")
    
    spark.createDataFrame([], trips_bronze_schema).write.format("delta").mode("overwrite").save(quarantine_path)
    spark.sql(f"CREATE TABLE quarantine_trips USING DELTA LOCATION '{quarantine_path}'")
    
    process_trips_silver(
        spark=spark,
        bronze_table="bronze_trips",
        silver_table="silver_trips",
        quarantine_table="quarantine_trips",
        checkpoint_base_path=checkpoints_path,
        trigger="availableNow"
    )
    
    # Read the quarantine table and assert
    quarantine_df = spark.read.table("quarantine_trips")
    
    # 3 records should be quarantined
    assert quarantine_df.count() == 3
    
    # Verify the failure reasons are populated
    invalid_reasons = quarantine_df.select("_quarantine_failed_rules").rdd.flatMap(lambda x: x).collect()
    
    assert any("vendor_id_not_null" in reason for reason in invalid_reasons if reason)
    assert any("valid_passenger_count" in reason for reason in invalid_reasons if reason)
    assert any("valid_fare" in reason for reason in invalid_reasons if reason)

    # Clean data should be in silver table
    silver_df = spark.read.table("silver_trips")
    assert silver_df.count() == 1

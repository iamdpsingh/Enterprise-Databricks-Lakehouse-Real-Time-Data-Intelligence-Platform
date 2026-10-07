import tempfile
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType, DoubleType
import pyspark.sql.functions as F
from src.pipelines.trips.silver_processing import process_trips_silver
import pytest

spark = SparkSession.builder.appName("Test2") \
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.0.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

with tempfile.TemporaryDirectory() as tmp_path:
    bronze_path = f"{tmp_path}/bronze"
    silver_path = f"{tmp_path}/silver"
    quarantine_path = f"{tmp_path}/quarantine"
    checkpoints_path = f"{tmp_path}/checkpoints"

    schema = StructType([
        StructField("vendor_id", StringType(), True),
        StructField("pickup_datetime", TimestampType(), True),
        StructField("dropoff_datetime", TimestampType(), True),
        StructField("passenger_count", IntegerType(), True),
        StructField("trip_distance", DoubleType(), True),
        StructField("fare_amount", DoubleType(), True),
        StructField("_ingested_at", TimestampType(), True)
    ])

    from datetime import datetime
    dt = datetime(2015, 10, 1, 12, 0, 0)
    bronze_data = [
        ("V1", dt, dt, 1, 2.5, 10.0, dt),     # Valid
        (None, dt, dt, 1, 2.5, 10.0, dt),     # Invalid
    ]
    bronze_df = spark.createDataFrame(bronze_data, schema)
    bronze_df.write.format("delta").save(bronze_path)
    spark.sql("DROP TABLE IF EXISTS bronze_trips")
    spark.sql(f"CREATE TABLE bronze_trips USING DELTA LOCATION '{bronze_path}'")

    spark.sql("DROP TABLE IF EXISTS silver_trips")
    spark.sql("DROP TABLE IF EXISTS quarantine_trips")
    
    # Do NOT pre-create the silver and quarantine tables
    # Let process_trips_silver create them via toTable()

    process_trips_silver(
        spark=spark,
        bronze_table="bronze_trips",
        silver_table="silver_trips",
        quarantine_table="quarantine_trips",
        checkpoint_base_path=checkpoints_path,
        trigger="availableNow"
    )

    print("COUNT:", spark.read.table("quarantine_trips").count())

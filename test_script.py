import sys
import os

# Create dummy SparkSession
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import pyspark.sql.functions as F

spark = SparkSession.builder.appName("Test").master("local[*]").getOrCreate()

schema = StructType([
    StructField("vendor_id", StringType(), True),
    StructField("pickup_datetime", TimestampType(), True),
    StructField("dropoff_datetime", TimestampType(), True),
    StructField("passenger_count", IntegerType(), True),
    StructField("trip_distance", DoubleType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("_ingested_at", TimestampType(), True)
])

df = spark.createDataFrame([], schema)

# apply_quality_rules equivalent
all_rules_passed_expr = F.col("passenger_count") > 0
failed_rules_expr = F.lit("valid_passenger_count")

quarantine_df = df.filter(~all_rules_passed_expr).withColumn(
    "_quarantine_failed_rules", failed_rules_expr
)

quarantine_df = quarantine_df.withColumn("_processed_at", F.current_timestamp())

print("SCHEMA:")
quarantine_df.printSchema()

# write it
import tempfile
with tempfile.TemporaryDirectory() as tmp_path:
    quarantine_path = f"{tmp_path}/quarantine"
    quarantine_schema = schema.add("_quarantine_failed_rules", StringType(), True).add("_processed_at", TimestampType(), True)
    spark.createDataFrame([], quarantine_schema).write.format("delta").mode("overwrite").save(quarantine_path)
    spark.sql(f"CREATE TABLE quarantine_trips USING DELTA LOCATION '{quarantine_path}'")
    
    quarantine_df.write.format("delta").option("mergeSchema", "true").mode("append").save(quarantine_path)
    print("SUCCESS")


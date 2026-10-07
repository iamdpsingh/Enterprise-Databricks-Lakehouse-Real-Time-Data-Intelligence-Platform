"""
Trips Pipeline: Gold Layer Processing
Aggregates the clean Silver data into business-ready Gold tables.
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.utilities.logger import logger


def process_trips_gold(
    spark: SparkSession,
    silver_table: str,
    gold_table: str,
    checkpoint_base_path: str,
    trigger: str = "availableNow"
) -> None:
    """
    Aggregates trips data to hourly metrics by pickup location.
    Calculates total revenue, trip count, and average distance.
    """
    logger.info(f"Starting Gold processing for Trips from {silver_table} to {gold_table}")
    
    # Read stream from Silver
    df = spark.readStream.table(silver_table)
    
    # Apply watermarking and tumbling window aggregation
    agg_df = (
        df.withWatermark("pickup_datetime", "2 hours")
        .groupBy(
            F.window(F.col("pickup_datetime"), "1 hour").alias("time_window"),
            F.col("pickup_location_id")
        )
        .agg(
            F.count("*").alias("total_trips"),
            F.sum("fare_amount").alias("total_revenue"),
            F.avg("trip_distance").alias("avg_distance"),
            F.sum("passenger_count").alias("total_passengers")
        )
    )
    
    # Format output for easier querying
    final_df = agg_df.select(
        F.col("time_window.start").alias("hour_start"),
        F.col("time_window.end").alias("hour_end"),
        F.col("pickup_location_id"),
        F.col("total_trips"),
        F.col("total_revenue"),
        F.col("avg_distance"),
        F.col("total_passengers")
    ).withColumn("_aggregated_at", F.current_timestamp())

    # Write aggregated data to Gold table
    query = (
        final_df.writeStream
        .format("delta")
        .option("checkpointLocation", f"{checkpoint_base_path}/trips_gold/checkpoints")
        .outputMode("append") # Append mode since we're using watermarked windowing
    )
    
    if trigger == "availableNow":
        query = query.trigger(availableNow=True)
    else:
        query = query.trigger(processingTime=trigger)
        
    streaming_query = query.table(gold_table)
    
    if trigger == "availableNow":
        streaming_query.awaitTermination()

    logger.info("Trips Gold processing complete.")

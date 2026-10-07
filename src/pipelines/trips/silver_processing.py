"""
Trips Pipeline: Silver Layer Processing
Cleans and validates the NYC Taxi Trips Bronze data.
Routes failed records to a quarantine table.
"""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.quality.rules import QualityRule, rule_is_not_null
from src.quality.quarantine import apply_quality_rules
from src.utilities.logger import logger


def get_trip_quality_rules() -> list[QualityRule]:
    """Define the data quality rules for NYC Taxi Trips."""
    return [
        rule_is_not_null("vendor_id"),
        rule_is_not_null("pickup_datetime"),
        rule_is_not_null("dropoff_datetime"),
        QualityRule(
            name="valid_passenger_count",
            description="Passenger count must be greater than 0",
            expression=F.col("passenger_count") > 0,
            is_fatal=True
        ),
        QualityRule(
            name="valid_fare",
            description="Fare amount cannot be negative",
            expression=F.col("fare_amount") >= 0,
            is_fatal=True
        ),
        QualityRule(
            name="valid_distance",
            description="Trip distance cannot be negative",
            expression=F.col("trip_distance") >= 0,
            is_fatal=True
        )
    ]


def process_trips_silver(
    spark: SparkSession,
    bronze_table: str,
    silver_table: str,
    quarantine_table: str,
    checkpoint_base_path: str,
    trigger: str = "availableNow"
) -> None:
    """
    Reads from Trips Bronze, applies data quality rules, and writes clean data to Silver
    and bad data to Quarantine.
    """
    logger.info(f"Starting Silver processing for Trips from {bronze_table}")
    
    # Read stream from Bronze
    df = spark.readStream.table(bronze_table)
    
    # Define rules
    rules = get_trip_quality_rules()
    
    # Apply rules
    valid_df, invalid_df = apply_quality_rules(df, rules)
    
    # Add silver processing metadata
    valid_df = valid_df.withColumn("_processed_at", F.current_timestamp())
    invalid_df = invalid_df.withColumn("_processed_at", F.current_timestamp())

    # Write clean data to Silver table
    clean_query = (
        valid_df.writeStream
        .format("delta")
        .option("checkpointLocation", f"{checkpoint_base_path}/trips_silver/checkpoints")
        .option("mergeSchema", "true")
    )
    
    # Write invalid data to Quarantine table
    quar_query = (
        invalid_df.writeStream
        .format("delta")
        .option("checkpointLocation", f"{checkpoint_base_path}/trips_quarantine/checkpoints")
        .option("mergeSchema", "true")
    )
    
    if trigger == "availableNow":
        clean_query = clean_query.trigger(availableNow=True)
        quar_query = quar_query.trigger(availableNow=True)
    else:
        clean_query = clean_query.trigger(processingTime=trigger)
        quar_query = quar_query.trigger(processingTime=trigger)
        
    sq_clean = clean_query.toTable(silver_table)
    sq_quar = quar_query.toTable(quarantine_table)
    
    if trigger == "availableNow":
        sq_clean.awaitTermination()
        sq_quar.awaitTermination()

    logger.info("Trips Silver processing complete.")

"""
Trips Pipeline: Bronze Layer Processing
Ingests NYC Taxi Trips data from GCS using Databricks Auto Loader.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from src.ingestion.autoloader import AutoLoaderStream, start_ingestion_stream
from src.utilities.logger import logger

def process_trips_bronze(
    spark: SparkSession,
    source_path: str,
    target_table: str,
    checkpoint_base_path: str,
    trigger: str = "availableNow"
) -> None:
    """
    Ingest raw NYC Taxi Trip parquet files from GCS into the Bronze layer.
    """
    logger.info(f"Starting Bronze processing for Trips from {source_path}")
    
    loader = AutoLoaderStream(spark)
    
    # Checkpoint and schema paths specific to this table
    checkpoint_path = f"{checkpoint_base_path}/trips_bronze/checkpoints"
    schema_path = f"{checkpoint_base_path}/trips_bronze/schema"
    
    # Options for parquet ingestion
    options = {
        "cloudFiles.maxFilesPerTrigger": 50  # Process in batches of 50 files for stability
    }
    
    # Read stream using Auto Loader
    stream_df = loader.create_read_stream(
        source_path=source_path,
        file_format="parquet",
        checkpoint_path=checkpoint_path,
        schema_location=schema_path,
        options=options
    )
    
    # Add ingestion metadata
    enriched_df = stream_df.withColumn("_ingested_at", current_timestamp())
    
    # Start the stream
    start_ingestion_stream(
        df=enriched_df,
        target_table=target_table,
        checkpoint_path=checkpoint_path,
        trigger=trigger,
        merge_schema=True
    )
    logger.info("Trips Bronze processing trigger complete.")

from pyspark.sql import SparkSession

from src.ingestion.autoloader import AutoLoaderStream, start_ingestion_stream
from src.utilities.logger import logger

def ingest_orders_bronze(spark: SparkSession, source_path: str, bronze_table: str, checkpoint_path: str) -> None:
    """
    Ingests raw JSON order files from cloud storage into the Bronze layer 
    using Databricks Auto Loader.
    """
    logger.info(f"Starting Bronze ingestion for Orders from {source_path}")
    
    # 1. Setup Auto Loader Stream
    autoloader = AutoLoaderStream(spark)
    stream_df = autoloader.create_read_stream(
        source_path=source_path,
        file_format="json",
        checkpoint_path=checkpoint_path,
        schema_location=f"{checkpoint_path}/schema"
    )
    
    # 2. Write Stream to Bronze Delta Table
    logger.info(f"Writing stream to Bronze table: {bronze_table}")
    start_ingestion_stream(
        df=stream_df,
        target_table=bronze_table,
        checkpoint_path=f"{checkpoint_path}/write",
        trigger="availableNow"
    )
    logger.info("Bronze ingestion for Orders completed.")

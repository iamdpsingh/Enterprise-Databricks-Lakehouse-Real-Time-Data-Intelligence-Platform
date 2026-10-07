from pyspark.sql import SparkSession

from pyspark.sql import SparkSession

from src.ingestion.autoloader import AutoLoaderStream, start_ingestion_stream
from src.utilities.logger import logger

def ingest_inventory_bronze(spark: SparkSession, source_path: str, bronze_table: str, checkpoint_path: str) -> None:
    """
    Ingests raw JSON inventory updates into the Bronze layer using Databricks Auto Loader.
    """
    logger.info(f"Starting Bronze ingestion for Inventory from {source_path}")
    
    loader = AutoLoaderStream(spark)
    stream_df = loader.create_read_stream(
        source_path=source_path,
        file_format="json",
        checkpoint_path=checkpoint_path,
        schema_location=f"{checkpoint_path}/schema"
    )
    
    logger.info(f"Writing stream to Bronze table: {bronze_table}")
    start_ingestion_stream(
        df=stream_df,
        target_table=bronze_table,
        checkpoint_path=f"{checkpoint_path}/write",
        trigger="availableNow"
    )
    
    logger.info("Bronze ingestion for Inventory completed.")

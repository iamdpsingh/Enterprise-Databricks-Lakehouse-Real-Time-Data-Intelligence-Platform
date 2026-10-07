from pyspark.sql import SparkSession

from src.ingestion.autoloader import read_stream_autoloader
from src.utilities.logger import logger

def ingest_orders_bronze(spark: SparkSession, source_path: str, bronze_table: str, checkpoint_path: str) -> None:
    """
    Ingests raw JSON order files from cloud storage into the Bronze layer 
    using Databricks Auto Loader.
    """
    logger.info(f"Starting Bronze ingestion for Orders from {source_path}")
    
    # 1. Setup Auto Loader Stream
    stream_df = read_stream_autoloader(
        spark=spark,
        source_path=source_path,
        data_format="json",
        schema_location=f"{checkpoint_path}/schema"
    )
    
    # 2. Write Stream to Bronze Delta Table
    logger.info(f"Writing stream to Bronze table: {bronze_table}")
    query = (
        stream_df.writeStream
        .format("delta")
        .option("checkpointLocation", f"{checkpoint_path}/write")
        .trigger(availableNow=True) # Recommended for scheduled batch streaming
        .table(bronze_table)
    )
    
    query.awaitTermination()
    logger.info("Bronze ingestion for Orders completed.")

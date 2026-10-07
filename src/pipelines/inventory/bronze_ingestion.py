from pyspark.sql import SparkSession

from src.ingestion.autoloader import read_stream_autoloader
from src.utilities.logger import logger

def ingest_inventory_bronze(spark: SparkSession, source_path: str, bronze_table: str, checkpoint_path: str) -> None:
    """
    Ingests raw JSON inventory updates into the Bronze layer using Databricks Auto Loader.
    """
    logger.info(f"Starting Bronze ingestion for Inventory from {source_path}")
    
    stream_df = read_stream_autoloader(
        spark=spark,
        source_path=source_path,
        data_format="json",
        schema_location=f"{checkpoint_path}/schema"
    )
    
    logger.info(f"Writing stream to Bronze table: {bronze_table}")
    query = (
        stream_df.writeStream
        .format("delta")
        .option("checkpointLocation", f"{checkpoint_path}/write")
        .trigger(availableNow=True)
        .table(bronze_table)
    )
    
    query.awaitTermination()
    logger.info("Bronze ingestion for Inventory completed.")

from pyspark.sql import SparkSession
from src.ingestion.autoloader import AutoLoaderStream, start_ingestion_stream
from src.utilities.logger import logger

def process_bronze(spark: SparkSession, source_path: str, target_table: str, checkpoint_path: str):
    """
    Bronze ingestion logic for Ethereum Web3.
    Refined for Day 1: Uses Auto Loader with schema rescue for dynamic blockchain events.
    """
    logger.info("Starting Ethereum Web3 Bronze Auto Loader")
    autoloader = AutoLoaderStream(spark)
    
    options = {
        "cloudFiles.schemaEvolutionMode": "rescue",
        "cloudFiles.inferColumnTypes": "true"
    }
    
    df = autoloader.create_read_stream(
        source_path=source_path,
        file_format="json",
        checkpoint_path=f"{checkpoint_path}/schema",
        schema_location=f"{checkpoint_path}/schema",
        options=options
    )
    
    start_ingestion_stream(
        df=df,
        target_table=target_table,
        checkpoint_path=checkpoint_path,
        trigger="availableNow", # Process batches as they arrive
        merge_schema=True
    )

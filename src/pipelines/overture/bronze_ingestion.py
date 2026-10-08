from pyspark.sql import SparkSession
from src.ingestion.autoloader import AutoLoaderStream, start_ingestion_stream
from src.utilities.logger import logger

def process_bronze(spark: SparkSession, source_path: str, target_table: str, checkpoint_path: str):
    """
    Bronze ingestion logic for Overture Maps.
    Refined for Day 1: Uses Auto Loader optimized for large Parquet geospatial datasets.
    """
    logger.info("Starting Overture Maps Bronze Auto Loader")
    autoloader = AutoLoaderStream(spark)
    
    options = {
        "cloudFiles.schemaEvolutionMode": "none", # Parquet has fixed schema
    }
    
    df = autoloader.create_read_stream(
        source_path=source_path,
        file_format="parquet",
        checkpoint_path=f"{checkpoint_path}/schema",
        schema_location=f"{checkpoint_path}/schema",
        options=options
    )
    
    start_ingestion_stream(
        df=df,
        target_table=target_table,
        checkpoint_path=checkpoint_path,
        trigger="1 minute",
        merge_schema=False
    )

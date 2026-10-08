from pyspark.sql import SparkSession
from src.ingestion.autoloader import AutoLoaderStream, start_ingestion_stream

def process_bronze(spark: SparkSession, source_path: str, target_table: str, checkpoint_path: str):
    """Bronze ingestion logic for Overture Maps."""
    autoloader = AutoLoaderStream(spark)
    df = autoloader.create_read_stream(
        source_path=source_path,
        file_format="parquet",
        checkpoint_path=f"{checkpoint_path}/schema",
        schema_location=f"{checkpoint_path}/schema"
    )
    start_ingestion_stream(
        df=df,
        target_table=target_table,
        checkpoint_path=checkpoint_path
    )

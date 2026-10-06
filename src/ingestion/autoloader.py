from typing import Dict, Any, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.streaming import DataStreamReader

from src.utilities.logger import logger

class AutoLoaderStream:
    """Wrapper for Databricks Auto Loader (cloudFiles) ingestion."""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark

    def create_read_stream(
        self,
        source_path: str,
        file_format: str,
        checkpoint_path: str,
        schema_location: str,
        options: Optional[Dict[str, Any]] = None
    ) -> DataFrame:
        """
        Creates a streaming DataFrame reading from cloud storage using Auto Loader.
        
        Args:
            source_path: The cloud URI to read from (e.g., 'gs://landing-zone/sales/').
            file_format: The format of the source files (json, csv, parquet, etc.).
            checkpoint_path: Path for structured streaming checkpointing.
            schema_location: Path for Auto Loader to store inferred schema.
            options: Additional format-specific or cloudFiles options.
            
        Returns:
            A streaming DataFrame.
        """
        logger.info(f"Initializing Auto Loader stream from {source_path}")
        
        # Default mandatory options for robustness and schema evolution
        base_options = {
            "cloudFiles.format": file_format,
            "cloudFiles.schemaLocation": schema_location,
            "cloudFiles.inferColumnTypes": "true",
            "cloudFiles.schemaEvolutionMode": "rescue", # Rescue unexpected columns
        }
        
        if options:
            base_options.update(options)

        reader: DataStreamReader = self.spark.readStream.format("cloudFiles")
        
        for key, value in base_options.items():
            reader = reader.option(key, str(value))
            
        return reader.load(source_path)

def start_ingestion_stream(
    df: DataFrame,
    target_table: str,
    checkpoint_path: str,
    trigger: str = "availableNow",
    merge_schema: bool = True
) -> None:
    """
    Starts the streaming query to write the ingested data to a Bronze Delta table.
    
    Args:
        df: The streaming DataFrame.
        target_table: The target Unity Catalog table (e.g., 'prod_catalog.bronze.sales').
        checkpoint_path: The checkpoint path for the write stream.
        trigger: Trigger timing ('availableNow' for micro-batch, '1 minute' for continuous).
        merge_schema: Whether to allow schema evolution in the target Delta table.
    """
    logger.info(f"Starting write stream to {target_table}")
    
    query = (
        df.writeStream
        .format("delta")
        .option("checkpointLocation", checkpoint_path)
        .option("mergeSchema", str(merge_schema).lower())
    )
    
    if trigger == "availableNow":
        query = query.trigger(availableNow=True)
    else:
        query = query.trigger(processingTime=trigger)
        
    streaming_query = query.table(target_table)
    
    if trigger == "availableNow":
        streaming_query.awaitTermination()

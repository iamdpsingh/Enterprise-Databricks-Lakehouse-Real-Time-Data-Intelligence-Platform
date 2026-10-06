from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def attach_bronze_metadata(df: DataFrame, source_system: str, batch_id: str) -> DataFrame:
    """
    Attaches mandatory audit metadata columns required for all Bronze tables.
    
    Args:
        df: The input DataFrame (from Auto Loader or API).
        source_system: Identifier for the source system (e.g., 'salesforce', 'erp').
        batch_id: A unique identifier for the ingestion run (UUID or job_run_id).
        
    Returns:
        DataFrame with added `_metadata_*` columns.
    """
    # Auto Loader automatically provides the _metadata hidden struct for cloud files
    # which contains file_path, file_modification_time, etc.
    # We extract these to top-level columns if they exist, otherwise use placeholders.
    
    has_file_metadata = "_metadata" in df.columns
    
    result_df = (
        df
        .withColumn("_metadata_source_system", F.lit(source_system))
        .withColumn("_metadata_ingestion_timestamp", F.current_timestamp())
        .withColumn("_metadata_batch_id", F.lit(batch_id))
    )
    
    if has_file_metadata:
        result_df = (
            result_df
            .withColumn("_metadata_file_path", F.col("_metadata.file_path"))
            .withColumn("_metadata_file_modified_time", F.col("_metadata.file_modification_time"))
        )
    else:
        # Fallback for API ingestion or non-file sources
        result_df = (
            result_df
            .withColumn("_metadata_file_path", F.lit("API/Stream"))
            .withColumn("_metadata_file_modified_time", F.lit(None).cast("timestamp"))
        )
        
    return result_df

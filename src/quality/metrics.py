from datetime import datetime
from typing import Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, LongType, DoubleType, BooleanType

from src.utilities.logger import logger
from src.utilities.config import app_config

def log_quality_metrics(
    spark: SparkSession,
    pipeline_name: str,
    table_name: str,
    run_id: str,
    total_records: int,
    quarantine_records: int,
    metrics_table: str = "monitoring.data_quality_metrics"
) -> None:
    """
    Logs aggregate data quality metrics to the centralized monitoring table.
    
    Args:
        spark: The SparkSession.
        pipeline_name: Name of the pipeline generating the metrics.
        table_name: Target table name being validated.
        run_id: Unique identifier for the job run.
        total_records: Total number of records processed.
        quarantine_records: Number of records routed to quarantine.
        metrics_table: The fully qualified name of the monitoring table.
    """
    passed_records = total_records - quarantine_records
    pass_rate = (passed_records / total_records) if total_records > 0 else 1.0
    
    logger.info(
        "Recording quality metrics",
        pipeline=pipeline_name,
        table=table_name,
        total=total_records,
        quarantine=quarantine_records,
        pass_rate=pass_rate
    )
    
    # Retrieve environment from config to determine the full catalog path
    env = app_config.get("environment", "dev")
    catalog_name = f"{env}_catalog"
    full_metrics_table = f"{catalog_name}.{metrics_table}"
    
    # Define schema for the metrics table
    schema = StructType([
        StructField("pipeline_name", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("run_id", StringType(), False),
        StructField("run_timestamp", TimestampType(), False),
        StructField("check_name", StringType(), False),
        StructField("total_records", LongType(), True),
        StructField("passed_records", LongType(), True),
        StructField("failed_records", LongType(), True),
        StructField("quarantine_records", LongType(), True),
        StructField("pass_rate", DoubleType(), True),
        StructField("is_alertable", BooleanType(), True),
        StructField("environment", StringType(), True)
    ])
    
    # Create the row data
    data = [(
        pipeline_name,
        table_name,
        run_id,
        datetime.utcnow(),
        "composite_fatal_rules", # Overall check name for the batch
        total_records,
        passed_records,
        quarantine_records, # Failed == Quarantined for our fatal rules
        quarantine_records,
        pass_rate,
        pass_rate < 0.95, # Example alert threshold: alert if < 95% pass rate
        env
    )]
    
    metrics_df = spark.createDataFrame(data, schema)
    
    try:
        (
            metrics_df.write
            .format("delta")
            .mode("append")
            .saveAsTable(full_metrics_table)
        )
    except Exception as e:
        # We don't want metric logging failure to fail the main pipeline
        logger.error(f"Failed to write metrics to {full_metrics_table}: {str(e)}")

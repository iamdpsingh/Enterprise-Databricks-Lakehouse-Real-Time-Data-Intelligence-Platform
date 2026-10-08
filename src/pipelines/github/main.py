from pyspark.sql import SparkSession
from .bronze_ingestion import process_bronze
from .silver_processing import process_silver
from .gold_aggregation import process_gold
from src.utilities.logger import logger

def run_pipeline():
    """Execute the full Medallion pipeline for github on GCP."""
    logger.info("Starting pipeline for github on GCP Databricks Serverless")
    spark = SparkSession.builder.appName("Github_Pipeline").getOrCreate()
    
    # Execute Bronze Layer (Day 1)
    logger.info("Executing Bronze Ingestion")
    # For Reddit we don't pass source_path, we pass token. 
    if 'github' == 'reddit':
        process_bronze(spark, token="placeholder_token", target_table="main.bronze.github")
    else:
        process_bronze(spark, source_path="gs://databrick-project-510903-landing-zone/github", target_table="main.bronze.github", checkpoint_path="/mnt/checkpoints/github/bronze")
    
    # Placeholders for Day 2
    # process_silver()
    # process_gold()
    
    logger.info("Pipeline for github completed.")

if __name__ == "__main__":
    run_pipeline()

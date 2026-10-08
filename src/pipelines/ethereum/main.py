from pyspark.sql import SparkSession
from .bronze_ingestion import process_bronze
from .silver_processing import process_silver
from .gold_aggregation import process_gold
from src.utilities.logger import logger

def run_pipeline():
    """Execute the full Medallion pipeline for ethereum on GCP."""
    logger.info("Starting pipeline for ethereum on GCP Databricks Serverless")
    spark = SparkSession.builder.appName("Ethereum_Pipeline").getOrCreate()
    
    # Execute Bronze Layer (Day 1)
    logger.info("Executing Bronze Ingestion")
    # For Reddit we don't pass source_path, we pass token. 
    if 'ethereum' == 'reddit':
        process_bronze(spark, token="placeholder_token", target_table="main.bronze.ethereum")
    else:
        process_bronze(spark, source_path="gs://databrick-project-510903-landing-zone/ethereum", target_table="main.bronze.ethereum", checkpoint_path="/mnt/checkpoints/ethereum/bronze")
    
    # Placeholders for Day 2
    # process_silver()
    # process_gold()
    
    logger.info("Pipeline for ethereum completed.")

if __name__ == "__main__":
    run_pipeline()

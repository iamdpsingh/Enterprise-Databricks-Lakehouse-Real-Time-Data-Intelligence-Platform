from pyspark.sql import SparkSession
from .bronze_ingestion import process_bronze
from .silver_processing import process_silver
from .gold_aggregation import process_gold
from src.utilities.logger import logger
from src.utilities.config import app_config

def run_pipeline():
    """Execute the full Medallion pipeline for reddit on GCP."""
    logger.info("Starting pipeline for reddit on GCP Databricks Serverless")
    spark = SparkSession.builder.appName("Reddit_Pipeline").getOrCreate()
    
    # Execute Bronze Layer (Day 1)
    logger.info("Executing Bronze Ingestion")
    # For Reddit we pull the secure token from .env via our config module
    if 'reddit' == 'reddit':
        token = app_config.get_secret("REDDIT_API_CLIENT_SECRET")
        process_bronze(spark, token=token, target_table="prod_catalog.reddit.bronze")
    else:
        process_bronze(spark, source_path="gs://databrick-project-510903-landing-zone/reddit", target_table="prod_catalog.reddit.bronze", checkpoint_path="/mnt/checkpoints/reddit/bronze")
    
    # Placeholders for Day 2
    # process_silver()
    # process_gold()
    
    logger.info("Pipeline for reddit completed.")

if __name__ == "__main__":
    run_pipeline()

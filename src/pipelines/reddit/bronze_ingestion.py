from pyspark.sql import SparkSession
from src.ingestion.api_reader import RestApiReader
from src.utilities.logger import logger

def process_bronze(spark: SparkSession, token: str, target_table: str):
    """
    Bronze ingestion logic for Reddit Pushshift via REST API.
    Refined for Day 1: Uses the custom RestApiReader for resilient API polling.
    """
    logger.info("Initializing Reddit Pushshift API Reader")
    reader = RestApiReader(spark, base_url="https://api.pushshift.io/reddit/search")
    
    if token:
        reader.set_auth_token(token)
    
    # Fetch recent submissions (micro-batch logic)
    records = reader.fetch_endpoint(endpoint="submission/", params={"size": 1000})
    df = reader.to_dataframe(records)
    
    logger.info(f"Writing Reddit data to Bronze Delta Table: {target_table}")
    # Write to Bronze layer with schema evolution enabled
    (df.write
       .format("delta")
       .mode("append")
       .option("mergeSchema", "true")
       .saveAsTable(target_table))

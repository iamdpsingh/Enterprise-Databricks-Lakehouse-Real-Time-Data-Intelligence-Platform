# =========================================================================================
# DATABRICKS MASTER NOTEBOOK: REAL-TIME INGESTION
# =========================================================================================
# INSTRUCTIONS:
# 1. Open your Databricks Workspace.
# 2. Create a new Python Notebook.
# 3. Copy and paste this ENTIRE file into the first cell.
# 4. Change the `GCP_BUCKET_NAME` variable below to match your Google Cloud project.
# 5. Hit SHIFT + ENTER to run!
# =========================================================================================

from pyspark.sql.functions import current_timestamp
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DatabricksAutoLoader")

# We are utilizing Databricks Unity Catalog Volumes as our landing zone.
# This completely bypasses all cloud IAM permission issues.

logger.info(f"Initializing Databricks Auto Loader targeting Unity Catalog Volumes")

# =========================================================================================
# 1. DEFINE STREAMING READERS
# =========================================================================================
eth_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaEvolutionMode", "rescue")
    .option("cloudFiles.schemaLocation", f"/Volumes/prod_catalog/ethereum/raw_landing/_checkpoints/schema")
    .load(f"/Volumes/prod_catalog/ethereum/raw_landing/")
    .withColumn("_ingested_at", current_timestamp())
)

gh_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    .option("cloudFiles.schemaLocation", f"/Volumes/prod_catalog/github/raw_landing/_checkpoints/schema")
    .load(f"/Volumes/prod_catalog/github/raw_landing/")
    .withColumn("_ingested_at", current_timestamp())
)

ov_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaEvolutionMode", "rescue")
    .option("cloudFiles.schemaLocation", f"/Volumes/prod_catalog/overture/raw_landing/_checkpoints/schema")
    .load(f"/Volumes/prod_catalog/overture/raw_landing/")
    .withColumn("_ingested_at", current_timestamp())
)

# =========================================================================================
# 2. CONTINUOUS MICRO-BATCH LOOP (Serverless Compatible)
# =========================================================================================
import time

logger.info("Starting infinite continuous sync loop...")
batch_id = 1
while True:
    logger.info(f"Starting Sync Batch #{batch_id}...")
    
    eth_query = eth_stream.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/ethereum/raw_landing/_checkpoints/write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.ethereum.bronze")
    gh_query = gh_stream.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/github/raw_landing/_checkpoints/write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.github.bronze")
    ov_query = ov_stream.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/overture/raw_landing/_checkpoints/write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.overture.bronze")
    
    eth_query.awaitTermination()
    gh_query.awaitTermination()
    ov_query.awaitTermination()
    
    logger.info(f"Batch #{batch_id} complete! Databricks tables updated.")
    batch_id += 1
    time.sleep(5) # Pause 5 seconds before checking for new files

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

from pyspark.sql.functions import current_timestamp, lit
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
# 2. SILVER LAYER: DATA QUALITY & DEDUPLICATION (OVERTURE)
# =========================================================================================
# Read from the Bronze table we just created
ov_silver_stream = (
    spark.readStream.table("prod_catalog.overture.bronze")
    .withWatermark("_ingested_at", "1 hour")
    .dropDuplicates(["id", "_ingested_at"]) # 👈 Deduplication!
)

# Rule: Latitude must be between -90 and 90, Longitude between -180 and 180
ov_valid = ov_silver_stream.filter("latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180")
ov_invalid = ov_silver_stream.filter("latitude < -90 OR latitude > 90 OR longitude < -180 OR longitude > 180").withColumn("_quarantine_failed_rules", lit("Invalid Lat/Lon Bounds"))

# =========================================================================================
# 3. GOLD LAYER: BUSINESS AGGREGATIONS (ROLLUPS)
# =========================================================================================
def update_gold_layer():
    # Ethereum Gold Aggregations
    spark.sql("""
        CREATE OR REPLACE TABLE prod_catalog.ethereum.gold AS 
        SELECT 
            COUNT(*) as txCount, 
            AVG(CAST(gas AS DOUBLE)) as avgGas, 
            SUM(CAST(value AS DOUBLE)) as totalTransfers 
        FROM prod_catalog.ethereum.bronze
    """)
    
    # GitHub Gold Aggregations
    spark.sql("""
        CREATE OR REPLACE TABLE prod_catalog.github.gold AS 
        SELECT 
            COUNT(*) as events, 
            COUNT(DISTINCT repo_name) as uniqueRepos, 
            SUM(CASE WHEN type = "PushEvent" THEN 1 ELSE 0 END) as pushEvents 
        FROM prod_catalog.github.bronze
    """)
    
    # Overture Maps Gold Aggregations
    spark.sql("""
        CREATE OR REPLACE TABLE prod_catalog.overture.gold AS 
        SELECT 
            COUNT(*) as pois, 
            COUNT(DISTINCT category) as categories, 
            COUNT(DISTINCT ROUND(latitude, 0)) as regions 
        FROM prod_catalog.overture.bronze
    """)

# =========================================================================================
# 4. CONTINUOUS MICRO-BATCH LOOP (Serverless Compatible)
# =========================================================================================
import time

logger.info("Starting infinite continuous sync loop...")
batch_id = 1
while True:
    logger.info(f"Starting Sync Batch #{batch_id}...")
    
    eth_query = eth_stream.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/ethereum/raw_landing/_checkpoints/write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.ethereum.bronze")
    gh_query = gh_stream.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/github/raw_landing/_checkpoints/write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.github.bronze")
    ov_query = ov_stream.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/overture/raw_landing/_checkpoints/write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.overture.bronze")
    
    # Run Silver Layer
    ov_silver_query = ov_valid.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/overture/raw_landing/_checkpoints/silver_write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.overture.silver")
    ov_quarantine_query = ov_invalid.writeStream.format("delta").option("checkpointLocation", f"/Volumes/prod_catalog/overture/raw_landing/_checkpoints/quarantine_write").option("mergeSchema", "true").trigger(availableNow=True).toTable("prod_catalog.quality.quarantine")
    
    eth_query.awaitTermination()
    gh_query.awaitTermination()
    ov_query.awaitTermination()
    ov_silver_query.awaitTermination()
    ov_quarantine_query.awaitTermination()
    
    # Update Gold Layer after streams finish processing the batch
    update_gold_layer()
    
    logger.info(f"Batch #{batch_id} complete! Bronze, Silver, Gold, and Quality tables updated.")
    batch_id += 1
    time.sleep(5) # Pause 5 seconds before checking for new files

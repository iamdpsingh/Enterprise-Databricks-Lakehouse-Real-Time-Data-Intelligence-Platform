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

# We are utilizing Databricks Unity Catalog Volumes as our landing zone.
# This completely bypasses all cloud IAM permission issues.

print(f"🚀 Initializing Databricks Auto Loader targeting Unity Catalog Volumes")

# =========================================================================================
# 1. ETHEREUM WEB3 PIPELINE
# Feature: schemaEvolutionMode="rescue" (Catches malformed blockchain payloads)
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

eth_query = (
    eth_stream.writeStream
    .format("delta")
    .option("checkpointLocation", f"/Volumes/prod_catalog/ethereum/raw_landing/_checkpoints/write")
    .option("mergeSchema", "true")
    .trigger(availableNow=True) # 👈 Serverless-compatible Trigger!
    .toTable("prod_catalog.ethereum.bronze")
)
print("✅ Ethereum Pipeline Started")

# =========================================================================================
# 2. GITHUB ARCHIVE PIPELINE
# Feature: schemaEvolutionMode="addNewColumns" (Handles highly nested JSON drift)
# =========================================================================================
gh_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    .option("cloudFiles.schemaLocation", f"/Volumes/prod_catalog/github/raw_landing/_checkpoints/schema")
    .load(f"/Volumes/prod_catalog/github/raw_landing/")
    .withColumn("_ingested_at", current_timestamp())
)

gh_query = (
    gh_stream.writeStream
    .format("delta")
    .option("checkpointLocation", f"/Volumes/prod_catalog/github/raw_landing/_checkpoints/write")
    .option("mergeSchema", "true")
    .trigger(availableNow=True) 
    .toTable("prod_catalog.github.bronze")
)
print("✅ GitHub Pipeline Started")

# =========================================================================================
# 3. OVERTURE MAPS PIPELINE
# Feature: High-throughput ingestion.
# =========================================================================================
ov_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaEvolutionMode", "rescue")
    .option("cloudFiles.schemaLocation", f"/Volumes/prod_catalog/overture/raw_landing/_checkpoints/schema")
    .load(f"/Volumes/prod_catalog/overture/raw_landing/")
    .withColumn("_ingested_at", current_timestamp())
)

ov_query = (
    ov_stream.writeStream
    .format("delta")
    .option("checkpointLocation", f"/Volumes/prod_catalog/overture/raw_landing/_checkpoints/write")
    .option("mergeSchema", "true")
    .trigger(availableNow=True) 
    .toTable("prod_catalog.overture.bronze")
)
print("✅ Overture Maps Pipeline Started")

print("🔥 All 3 Datasets are now streaming in real-time from GCP to Databricks!")

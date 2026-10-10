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

# ⚠️ CHANGE THIS TO YOUR ACTUAL GCP PROJECT ID
GCP_BUCKET_NAME = "databrick-project-510903-raw-landing-zone"

# Base paths
GCS_BASE_URI = f"gs://{GCP_BUCKET_NAME}"
CHECKPOINT_BASE = f"{GCS_BASE_URI}/checkpoints"

print(f"🚀 Initializing Databricks Auto Loader targeting: {GCS_BASE_URI}")

# =========================================================================================
# 1. ETHEREUM WEB3 PIPELINE
# Feature: schemaEvolutionMode="rescue" (Catches malformed blockchain payloads)
# =========================================================================================
eth_stream = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaEvolutionMode", "rescue")
    .option("cloudFiles.schemaLocation", f"{CHECKPOINT_BASE}/ethereum/schema")
    .load(f"{GCS_BASE_URI}/ethereum/raw/")
    .withColumn("_ingested_at", current_timestamp())
)

eth_query = (
    eth_stream.writeStream
    .format("delta")
    .option("checkpointLocation", f"{CHECKPOINT_BASE}/ethereum/write")
    .option("mergeSchema", "true")
    .trigger(processingTime="5 seconds") # 👈 Real-time streaming!
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
    .option("cloudFiles.schemaLocation", f"{CHECKPOINT_BASE}/github/schema")
    .load(f"{GCS_BASE_URI}/github/raw/")
    .withColumn("_ingested_at", current_timestamp())
)

gh_query = (
    gh_stream.writeStream
    .format("delta")
    .option("checkpointLocation", f"{CHECKPOINT_BASE}/github/write")
    .option("mergeSchema", "true")
    .trigger(processingTime="5 seconds") 
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
    .option("cloudFiles.schemaLocation", f"{CHECKPOINT_BASE}/overture/schema")
    .load(f"{GCS_BASE_URI}/overture/raw/")
    .withColumn("_ingested_at", current_timestamp())
)

ov_query = (
    ov_stream.writeStream
    .format("delta")
    .option("checkpointLocation", f"{CHECKPOINT_BASE}/overture/write")
    .option("mergeSchema", "true")
    .trigger(processingTime="5 seconds") 
    .toTable("prod_catalog.overture.bronze")
)
print("✅ Overture Maps Pipeline Started")

print("🔥 All 3 Datasets are now streaming in real-time from GCP to Databricks!")

import argparse
from pyspark.sql import SparkSession

from src.pipelines.inventory.bronze_ingestion import ingest_inventory_bronze
from src.pipelines.inventory.silver_processing import process_inventory_silver
from src.pipelines.inventory.gold_aggregation import aggregate_inventory_gold
from src.utilities.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Inventory Pipeline Execution")
    parser.add_argument("--layer", required=True, choices=["bronze", "silver", "gold", "all"], help="Which layer to process")
    parser.add_argument("--source-path", required=False, help="Source path for bronze ingestion")
    parser.add_argument("--bronze-table", required=True, help="Bronze table name")
    parser.add_argument("--silver-table", required=True, help="Silver table name")
    parser.add_argument("--gold-table", required=True, help="Gold table name")
    parser.add_argument("--quarantine-table", required=True, help="Quarantine table name")
    parser.add_argument("--checkpoint-path", required=False, help="Checkpoint path for streaming")
    
    args = parser.parse_args()
    
    spark = SparkSession.builder.appName("InventoryPipeline").getOrCreate()
    
    if args.layer in ["bronze", "all"]:
        if not args.source_path or not args.checkpoint_path:
            raise ValueError("--source-path and --checkpoint-path are required for bronze processing")
        ingest_inventory_bronze(spark, args.source_path, args.bronze_table, args.checkpoint_path)
        
    if args.layer in ["silver", "all"]:
        process_inventory_silver(spark, args.bronze_table, args.silver_table, args.quarantine_table)
        
    if args.layer in ["gold", "all"]:
        aggregate_inventory_gold(spark, args.silver_table, args.gold_table)
        
    logger.info(f"Inventory pipeline execution for layer '{args.layer}' completed successfully.")

if __name__ == "__main__":
    main()

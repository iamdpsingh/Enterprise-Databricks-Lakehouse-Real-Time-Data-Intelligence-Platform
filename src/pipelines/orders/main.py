import argparse
from pyspark.sql import SparkSession

from src.pipelines.orders.bronze_ingestion import ingest_orders_bronze
from src.pipelines.orders.silver_processing import process_orders_silver
from src.pipelines.orders.gold_aggregation import aggregate_orders_gold
from src.utilities.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Orders Pipeline Execution")
    parser.add_argument("--layer", required=True, choices=["bronze", "silver", "gold", "all"], help="Which layer to process")
    parser.add_argument("--source-path", required=False, help="Source path for bronze ingestion")
    parser.add_argument("--bronze-table", required=True, help="Bronze table name")
    parser.add_argument("--silver-table", required=True, help="Silver table name")
    parser.add_argument("--gold-table", required=True, help="Gold table name")
    parser.add_argument("--quarantine-table", required=True, help="Quarantine table name")
    parser.add_argument("--checkpoint-path", required=False, help="Checkpoint path for streaming")
    
    args = parser.parse_args()
    
    spark = SparkSession.builder.appName("OrdersPipeline").getOrCreate()
    
    if args.layer in ["bronze", "all"]:
        if not args.source_path or not args.checkpoint_path:
            raise ValueError("--source-path and --checkpoint-path are required for bronze processing")
        ingest_orders_bronze(spark, args.source_path, args.bronze_table, args.checkpoint_path)
        
    if args.layer in ["silver", "all"]:
        process_orders_silver(spark, args.bronze_table, args.silver_table, args.quarantine_table)
        
    if args.layer in ["gold", "all"]:
        aggregate_orders_gold(spark, args.silver_table, args.gold_table)
        
    logger.info(f"Orders pipeline execution for layer '{args.layer}' completed successfully.")

if __name__ == "__main__":
    main()

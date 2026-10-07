"""
Trips Pipeline: Main Entrypoint
Orchestrates the Bronze, Silver, and Gold layer processing for NYC Taxi Trips.
"""
import argparse
from pyspark.sql import SparkSession

from src.utilities.logger import logger
from src.pipelines.trips.bronze_processing import process_trips_bronze
from src.pipelines.trips.silver_processing import process_trips_silver
from src.pipelines.trips.gold_processing import process_trips_gold

def parse_args():
    parser = argparse.ArgumentParser(description="Trips Medallion Pipeline")
    parser.add_argument("--layer", required=True, choices=["bronze", "silver", "gold"], help="Which layer to process")
    parser.add_argument("--source-path", default="", help="Path to raw trips data (for bronze layer)")
    parser.add_argument("--bronze-table", required=True, help="Bronze table name")
    parser.add_argument("--silver-table", required=True, help="Silver table name")
    parser.add_argument("--gold-table", required=True, help="Gold table name")
    parser.add_argument("--quarantine-table", required=True, help="Quarantine table name")
    parser.add_argument("--checkpoint-path", default="", help="Base path for structured streaming checkpoints")
    parser.add_argument("--trigger", default="availableNow", help="Streaming trigger timing (e.g. availableNow, 1 minute)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Initialize Spark Session
    spark = SparkSession.builder.appName(f"TripsPipeline_{args.layer.capitalize()}").getOrCreate()
    
    logger.info(f"Starting Trips Pipeline: {args.layer} layer")
    
    try:
        if args.layer == "bronze":
            if not args.source_path or not args.checkpoint_path:
                raise ValueError("--source-path and --checkpoint-path are required for bronze layer")
                
            process_trips_bronze(
                spark=spark,
                source_path=args.source_path,
                target_table=args.bronze_table,
                checkpoint_base_path=args.checkpoint_path,
                trigger=args.trigger
            )
            
        elif args.layer == "silver":
            if not args.checkpoint_path:
                raise ValueError("--checkpoint-path is required for silver layer")
                
            process_trips_silver(
                spark=spark,
                bronze_table=args.bronze_table,
                silver_table=args.silver_table,
                quarantine_table=args.quarantine_table,
                checkpoint_base_path=args.checkpoint_path,
                trigger=args.trigger
            )
            
        elif args.layer == "gold":
            if not args.checkpoint_path:
                raise ValueError("--checkpoint-path is required for gold layer")
                
            process_trips_gold(
                spark=spark,
                silver_table=args.silver_table,
                gold_table=args.gold_table,
                checkpoint_base_path=args.checkpoint_path,
                trigger=args.trigger
            )
            
        logger.info(f"Successfully completed Trips Pipeline: {args.layer} layer")
        
    except Exception as e:
        logger.error(f"Error in Trips Pipeline {args.layer} layer: {str(e)}")
        raise e

if __name__ == "__main__":
    main()

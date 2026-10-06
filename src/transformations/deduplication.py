from typing import List

from pyspark.sql import DataFrame
from pyspark.sql.window import Window
from pyspark.sql import functions as F

from src.utilities.logger import logger

def deduplicate_keep_latest(
    df: DataFrame, 
    partition_cols: List[str], 
    order_by_col: str, 
    ascending: bool = False
) -> DataFrame:
    """
    Deduplicates a DataFrame by keeping only the latest record for each group defined by partition_cols.
    
    Args:
        df: The input DataFrame.
        partition_cols: List of column names that define the unique entity (e.g., ['customer_id']).
        order_by_col: The column used to determine the "latest" record (e.g., 'updated_at').
        ascending: If False (default), keeps the row with the maximum value in order_by_col.
        
    Returns:
        Deduplicated DataFrame.
    """
    logger.info(f"Deduplicating by {partition_cols}, ordering by {order_by_col} (asc={ascending})")
    
    # Create the window spec
    order_col = F.col(order_by_col).asc() if ascending else F.col(order_by_col).desc()
    
    window_spec = Window.partitionBy(*[F.col(c) for c in partition_cols]).orderBy(order_col)
    
    # Add a row number, filter for rn=1, then drop the row number column
    return (
        df.withColumn("_rn", F.row_number().over(window_spec))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from src.utilities.logger import logger

def soft_delete_records(
    target_table: DeltaTable,
    deleted_keys_df: DataFrame,
    primary_keys: list[str],
    is_deleted_col: str = "is_deleted"
) -> None:
    """
    Performs a soft delete by setting a flag on records in the target table
    that match the keys provided in deleted_keys_df.
    
    Args:
        target_table: The DeltaTable instance to update.
        deleted_keys_df: DataFrame containing the primary keys of records to soft delete.
        primary_keys: List of columns that uniquely identify a logical record.
        is_deleted_col: The name of the boolean column indicating soft deletion.
    """
    logger.info(f"Performing soft delete on target table based on keys: {primary_keys}")
    
    merge_condition = " AND ".join([f"target.{pk} = source.{pk}" for pk in primary_keys])
    
    (
        target_table.alias("target")
        .merge(
            deleted_keys_df.alias("source"),
            merge_condition
        )
        .whenMatchedUpdate(
            set={
                is_deleted_col: "true"
            }
        )
        .execute()
    )


def hard_delete_records(
    target_table: DeltaTable,
    deleted_keys_df: DataFrame,
    primary_keys: list[str]
) -> None:
    """
    Performs a hard delete by removing records from the target table
    that match the keys provided in deleted_keys_df.
    
    Args:
        target_table: The DeltaTable instance to update.
        deleted_keys_df: DataFrame containing the primary keys of records to hard delete.
        primary_keys: List of columns that uniquely identify a logical record.
    """
    logger.info(f"Performing hard delete on target table based on keys: {primary_keys}")
    
    merge_condition = " AND ".join([f"target.{pk} = source.{pk}" for pk in primary_keys])
    
    (
        target_table.alias("target")
        .merge(
            deleted_keys_df.alias("source"),
            merge_condition
        )
        .whenMatchedDelete()
        .execute()
    )

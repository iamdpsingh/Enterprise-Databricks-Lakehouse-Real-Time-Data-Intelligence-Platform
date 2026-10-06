from pyspark.sql import DataFrame
from delta.tables import DeltaTable

def upsert_scd1(
    target_table: DeltaTable,
    source_df: DataFrame,
    primary_keys: list[str]
) -> None:
    """
    Performs a Type 1 Slowly Changing Dimension (SCD1) UPSERT into a Delta table.
    Overwrites existing records with the same primary keys; inserts new ones.
    
    Args:
        target_table: The DeltaTable instance to update.
        source_df: The source DataFrame containing the new/updated records.
        primary_keys: List of columns that uniquely identify a record.
    """
    # Construct the merge condition dynamically based on the primary keys
    # Example: "target.id = source.id AND target.tenant_id = source.tenant_id"
    merge_condition = " AND ".join([f"target.{pk} = source.{pk}" for pk in primary_keys])
    
    (
        target_table.alias("target")
        .merge(
            source_df.alias("source"),
            merge_condition
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )

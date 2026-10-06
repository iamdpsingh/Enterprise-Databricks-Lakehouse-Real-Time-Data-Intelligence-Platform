from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from delta.tables import DeltaTable

def merge_scd2(
    target_table: DeltaTable,
    source_df: DataFrame,
    primary_keys: list[str],
    update_timestamp_col: str = "updated_at",
    is_current_col: str = "is_current",
    valid_from_col: str = "valid_from",
    valid_to_col: str = "valid_to"
) -> None:
    """
    Performs a Type 2 Slowly Changing Dimension (SCD2) MERGE into a Delta table.
    Retains historical records by expiring old rows and inserting new current rows.
    
    This uses the standard Databricks SCD2 pattern (union of updates + inserts).
    
    Args:
        target_table: The DeltaTable instance to update.
        source_df: The source DataFrame containing the new/updated records.
        primary_keys: List of columns that uniquely identify a logical record.
        update_timestamp_col: The column defining the time of the change in the source.
    """
    # 1. Identify updates. We need to create a dummy record for the old version to expire it,
    # and a new record for the current version.
    
    # Condition to match on primary keys
    pk_condition = " AND ".join([f"target.{pk} = source.{pk}" for pk in primary_keys])
    
    # We join source with target to find existing records that are currently active
    # and are being updated in this batch.
    staged_updates = (
        source_df.alias("source")
        .join(
            target_table.toDF().alias("target"),
            [F.expr(f"source.{pk} <=> target.{pk}") for pk in primary_keys],
            "left"
        )
        .where(f"target.{is_current_col} = true")
        # We also want new records (where target is null)
        .where(f"target.{primary_keys[0]} IS NULL OR source.{update_timestamp_col} > target.{update_timestamp_col}")
        .selectExpr("source.*") 
    )
    
    # To implement SCD2 with a single merge, we union:
    # A. The records we want to insert (both brand new records and updated records)
    # B. A dummy representation of the updated records to trigger the expiration of the old records
    
    # For dummy records, we nullify the primary keys so they trigger the "whenMatched" 
    # update, but we need the join key to resolve. So we use a merge key.
    
    # Create the merge dataframe
    merge_key_cols = [f"{pk}_mergeKey" for pk in primary_keys]
    
    inserts = staged_updates.select(
        *[F.col(c).alias(c) for c in staged_updates.columns],
        *[F.col(pk).alias(f"{pk}_mergeKey") for pk in primary_keys]
    )
    
    dummies = staged_updates.select(
        *[F.col(c).alias(c) for c in staged_updates.columns],
        *[F.lit(None).alias(f"{pk}_mergeKey") for pk in primary_keys]
    )
    
    staged_df = inserts.unionByName(dummies)
    
    # Construct merge condition using the merge keys
    merge_condition = " AND ".join([f"target.{pk} = source.{pk}_mergeKey" for pk in primary_keys])
    
    # Execute the merge
    (
        target_table.alias("target")
        .merge(
            staged_df.alias("source"),
            merge_condition
        )
        .whenMatchedUpdate(
            condition=f"target.{is_current_col} = true AND " + " AND ".join([f"target.{pk} = source.{pk}" for pk in primary_keys]),
            set={
                is_current_col: "false",
                valid_to_col: f"source.{update_timestamp_col}"
            }
        )
        .whenNotMatchedInsert(
            values={
                # Insert all columns from source
                **{c: f"source.{c}" for c in source_df.columns},
                is_current_col: "true",
                valid_from_col: f"source.{update_timestamp_col}",
                valid_to_col: "null"
            }
        )
        .execute()
    )

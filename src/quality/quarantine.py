from typing import List, Tuple

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.utilities.logger import logger
from .rules import QualityRule, build_composite_rule_expression, extract_failed_rule_names

def apply_quality_rules(
    df: DataFrame, 
    rules: List[QualityRule],
    quarantine_reason_col: str = "_quarantine_failed_rules"
) -> Tuple[DataFrame, DataFrame]:
    """
    Evaluates quality rules against a DataFrame and splits it into valid and quarantined records.

    Args:
        df: The input PySpark DataFrame.
        rules: A list of QualityRule objects to evaluate.
        quarantine_reason_col: The name of the column to append to quarantined records 
                               containing the names of the failed rules.

    Returns:
        A tuple containing:
        - valid_df: DataFrame of records that passed all fatal rules.
        - quarantine_df: DataFrame of records that failed one or more fatal rules,
                         with an appended column indicating which rules failed.
    """
    if not rules:
        logger.info("No quality rules provided. All records marked as valid.")
        # Return empty df for quarantine with the expected schema
        empty_quarantine = df.withColumn(quarantine_reason_col, F.lit("").cast("string")).limit(0)
        return df, empty_quarantine

    logger.info(f"Applying {len(rules)} quality rules to dataset.")
    
    # Build expressions
    all_rules_passed_expr = build_composite_rule_expression(rules)
    failed_rules_expr = extract_failed_rule_names(rules)

    # We evaluate the rules once and cache the result if we expect the DF to be large,
    # but for simplicity in this function, we'll just apply the filters.
    
    # Valid records: passing all fatal rules
    valid_df = df.filter(all_rules_passed_expr)
    
    # Quarantined records: failing at least one fatal rule
    quarantine_df = df.filter(~all_rules_passed_expr).withColumn(
        quarantine_reason_col, failed_rules_expr
    )
    
    return valid_df, quarantine_df

def write_to_quarantine(
    df: DataFrame, 
    quarantine_table_name: str,
    merge_schema: bool = True
) -> None:
    """
    Writes quarantined records to a Delta table in Unity Catalog.
    
    Args:
        df: The DataFrame of quarantined records.
        quarantine_table_name: The full 3-level Unity Catalog table name (e.g., prod_catalog.quarantine.sales).
        merge_schema: Whether to merge schema changes automatically.
    """
    if df.isEmpty():
        logger.info("No quarantined records to write.")
        return
        
    logger.warning(f"Writing quarantined records to {quarantine_table_name}")
    
    # Append to quarantine table
    (
        df.write
        .format("delta")
        .mode("append")
        .option("mergeSchema", str(merge_schema).lower())
        .saveAsTable(quarantine_table_name)
    )

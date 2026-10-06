from typing import Dict, List, Optional
from dataclasses import dataclass

from pyspark.sql import Column
from pyspark.sql import functions as F

@dataclass
class QualityRule:
    """Represents a single data quality rule to be evaluated against a DataFrame."""
    name: str
    description: str
    expression: Column
    is_fatal: bool = True

def rule_is_not_null(column_name: str, is_fatal: bool = True) -> QualityRule:
    """Creates a rule that checks if a column is not null."""
    return QualityRule(
        name=f"{column_name}_not_null",
        description=f"Ensures column '{column_name}' contains no null values",
        expression=F.col(column_name).isNotNull(),
        is_fatal=is_fatal,
    )

def rule_matches_regex(column_name: str, pattern: str, is_fatal: bool = True) -> QualityRule:
    """Creates a rule that checks if a string column matches a regex pattern."""
    return QualityRule(
        name=f"{column_name}_matches_regex",
        description=f"Ensures column '{column_name}' matches pattern '{pattern}'",
        expression=F.col(column_name).rlike(pattern),
        is_fatal=is_fatal,
    )

def rule_is_unique(column_name: str, is_fatal: bool = True) -> QualityRule:
    """
    Creates a rule for uniqueness. 
    Note: Standard column expressions cannot compute uniqueness across rows easily inline.
    This rule usually implies a window function or distinct count evaluation at the dataset level.
    For inline streaming/row-level checks, uniqueness is typically handled via constraints 
    or deduplication steps rather than a boolean column expression.
    """
    pass # Placeholder for complex dataset-level rules

def build_composite_rule_expression(rules: List[QualityRule]) -> Column:
    """
    Combines multiple rules into a single expression that evaluates to True 
    if ALL fatal rules pass.
    """
    if not rules:
        return F.lit(True)
        
    fatal_expressions = [rule.expression for rule in rules if rule.is_fatal]
    
    if not fatal_expressions:
        return F.lit(True)
        
    # AND all fatal expressions together
    combined_expr = fatal_expressions[0]
    for expr in fatal_expressions[1:]:
        combined_expr = combined_expr & expr
        
    return combined_expr

def extract_failed_rule_names(rules: List[QualityRule]) -> Column:
    """
    Creates an expression that returns a comma-separated string of the names
    of any rules that failed for a given row.
    """
    if not rules:
        return F.lit(None).cast("string")
        
    failed_names_exprs = [
        F.when(~rule.expression, F.lit(rule.name)).otherwise(F.lit(None))
        for rule in rules
    ]
    
    # Use array_remove to filter out nulls, then concat_ws to join them
    array_expr = F.array(*failed_names_exprs)
    clean_array = F.expr("filter({}, x -> x IS NOT NULL)".format(array_expr._jc.toString() if hasattr(array_expr, "_jc") else "array_placeholder"))
    
    # Simpler PySpark native approach without raw expr string manipulation:
    # array_compact removes nulls in PySpark 3.4+
    if hasattr(F, "array_compact"):
        return F.array_join(F.array_compact(F.array(*failed_names_exprs)), ",")
    else:
        # Fallback for older Spark versions
        return F.concat_ws(",", *failed_names_exprs)

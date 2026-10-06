from typing import List

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DataType

def trim_string_columns(df: DataFrame) -> DataFrame:
    """
    Trims leading and trailing whitespace from all string columns in the DataFrame.
    """
    string_cols = [f.name for f in df.schema.fields if f.dataType.simpleString() == "string"]
    
    for col_name in string_cols:
        df = df.withColumn(col_name, F.trim(F.col(col_name)))
        
    return df

def standardize_nulls(df: DataFrame, null_equivalents: List[str] = None) -> DataFrame:
    """
    Converts common string representations of null ('N/A', 'NULL', '', etc.) to actual SQL NULLs.
    """
    if null_equivalents is None:
        null_equivalents = ["", "N/A", "NA", "NULL", "null", "None", "NaN"]
        
    string_cols = [f.name for f in df.schema.fields if f.dataType.simpleString() == "string"]
    
    for col_name in string_cols:
        # If the value is in the equivalents list, return NULL, else keep the value
        df = df.withColumn(
            col_name,
            F.when(F.col(col_name).isin(null_equivalents), F.lit(None)).otherwise(F.col(col_name))
        )
        
    return df

def cast_column(df: DataFrame, column_name: str, target_type: DataType, fallback_null: bool = True) -> DataFrame:
    """
    Safely casts a column to a target type.
    
    Args:
        df: Input DataFrame.
        column_name: Name of the column to cast.
        target_type: PySpark DataType to cast to.
        fallback_null: If True, invalid casts become NULL. If False, we try to fail or keep as is.
                       (PySpark's native cast() naturally falls back to null on failure).
    """
    return df.withColumn(column_name, F.col(column_name).cast(target_type))

def standardize_timestamps(df: DataFrame, column_name: str, format_str: str = "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'") -> DataFrame:
    """
    Parses a string column into a proper Timestamp type based on a given format.
    """
    return df.withColumn(column_name, F.to_timestamp(F.col(column_name), format_str))

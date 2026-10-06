from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def mask_string(df: DataFrame, column_name: str, visible_chars: int = 4, mask_char: str = "*") -> DataFrame:
    """
    Partially masks a string column, leaving only the last `visible_chars` unmasked.
    Typically used for SSNs, credit cards, or phone numbers at rest in Silver.
    (Note: Unity Catalog dynamic data masking is preferred for read-time masking).
    """
    return df.withColumn(
        column_name,
        F.when(
            F.col(column_name).isNotNull() & (F.length(F.col(column_name)) > visible_chars),
            F.concat(
                F.expr(f"repeat('{mask_char}', length({column_name}) - {visible_chars})"),
                F.expr(f"right({column_name}, {visible_chars})")
            )
        ).otherwise(F.col(column_name))
    )

def pseudonymize_email(df: DataFrame, column_name: str) -> DataFrame:
    """
    Masks the local part of an email address, keeping the domain intact.
    e.g., john.doe@example.com -> j***@example.com
    """
    return df.withColumn(
        column_name,
        F.when(
            F.col(column_name).contains("@"),
            F.concat(
                F.substring(F.split(F.col(column_name), "@")[0], 1, 1),
                F.lit("***@"),
                F.split(F.col(column_name), "@")[1]
            )
        ).otherwise(F.col(column_name))
    )

def hash_identifier(df: DataFrame, column_name: str, salt: str = "") -> DataFrame:
    """
    Applies a SHA-256 hash to a column (e.g., device_id, ip_address).
    """
    return df.withColumn(
        column_name,
        F.sha2(F.concat(F.col(column_name), F.lit(salt)), 256)
    )

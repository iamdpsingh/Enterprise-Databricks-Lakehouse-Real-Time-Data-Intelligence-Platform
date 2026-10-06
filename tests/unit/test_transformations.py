import pytest
from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from src.transformations.cleaning import trim_string_columns, standardize_nulls
from src.transformations.deduplication import deduplicate_keep_latest
from src.transformations.pii_masking import mask_string, pseudonymize_email

def test_trim_string_columns(spark):
    data = [Row(id=1, name="  Alice  ", city="Bobville ")]
    df = spark.createDataFrame(data)
    
    result = trim_string_columns(df).collect()[0]
    
    assert result.name == "Alice"
    assert result.city == "Bobville"

def test_standardize_nulls(spark):
    data = [
        Row(id=1, value="N/A"),
        Row(id=2, value=""),
        Row(id=3, value="Valid")
    ]
    df = spark.createDataFrame(data)
    
    result = standardize_nulls(df).collect()
    
    assert result[0].value is None
    assert result[1].value is None
    assert result[2].value == "Valid"

def test_deduplicate_keep_latest(spark):
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("updated_at", IntegerType(), True),
        StructField("val", StringType(), True)
    ])
    
    data = [
        Row(id=1, updated_at=100, val="old"),
        Row(id=1, updated_at=200, val="new"),  # Latest for id=1
        Row(id=2, updated_at=150, val="keep")  # Only record for id=2
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # We want max updated_at, so ascending=False
    result_df = deduplicate_keep_latest(df, partition_cols=["id"], order_by_col="updated_at", ascending=False)
    
    results = result_df.orderBy("id").collect()
    
    assert len(results) == 2
    assert results[0].id == 1
    assert results[0].val == "new"
    assert results[1].id == 2
    assert results[1].val == "keep"

def test_mask_string(spark):
    data = [
        Row(ssn="123456789"),
        Row(ssn="123") # Too short to mask
    ]
    df = spark.createDataFrame(data)
    
    result = mask_string(df, "ssn", visible_chars=4, mask_char="*").collect()
    
    assert result[0].ssn == "*****6789"
    assert result[1].ssn == "123"

def test_pseudonymize_email(spark):
    data = [
        Row(email="john.doe@example.com"),
        Row(email="jane@company.org"),
        Row(email="invalid_email")
    ]
    df = spark.createDataFrame(data)
    
    result = pseudonymize_email(df, "email").collect()
    
    assert result[0].email == "j***@example.com"
    assert result[1].email == "j***@company.org"
    assert result[2].email == "invalid_email"

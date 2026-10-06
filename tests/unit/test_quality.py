import pytest
from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

from src.quality.rules import expect_column_to_not_be_null, expect_column_values_to_be_in_set
from src.quality.quarantine import QuarantineManager

def test_expect_column_to_not_be_null():
    """Test generating a NOT NULL DLT constraint."""
    rule = expect_column_to_not_be_null("customer_id")
    assert rule["name"] == "valid_customer_id"
    assert rule["constraint"] == "customer_id IS NOT NULL"
    assert rule["action"] == "drop"

def test_expect_column_to_not_be_null_custom_action():
    """Test generating a NOT NULL constraint with fail action."""
    rule = expect_column_to_not_be_null("id", action="fail")
    assert rule["name"] == "valid_id"
    assert rule["constraint"] == "id IS NOT NULL"
    assert rule["action"] == "fail"

def test_expect_column_values_to_be_in_set():
    """Test generating an IN SET DLT constraint."""
    rule = expect_column_values_to_be_in_set("status", ["ACTIVE", "PENDING"])
    assert rule["name"] == "valid_status"
    assert rule["constraint"] == "status IN ('ACTIVE', 'PENDING')"
    assert rule["action"] == "drop"

def test_quarantine_manager_split(spark):
    """Test splitting valid and invalid records using QuarantineManager."""
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("email", StringType(), True)
    ])
    
    data = [
        Row(id=1, email="test@example.com"),
        Row(id=2, email=None),  # Invalid email
        Row(id=None, email="bad@example.com")  # Invalid id
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # We want valid records to have BOTH id and email
    valid_df, quarantine_df = QuarantineManager.split_valid_invalid(
        df,
        rules=["id IS NOT NULL", "email IS NOT NULL"]
    )
    
    valid_records = valid_df.collect()
    quarantine_records = quarantine_df.collect()
    
    assert len(valid_records) == 1
    assert valid_records[0].id == 1
    
    assert len(quarantine_records) == 2
    # Verify the quarantine column was added
    assert "quarantine_reasons" in quarantine_df.columns

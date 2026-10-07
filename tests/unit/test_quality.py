import pytest
from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, IntegerType, StringType
from pyspark.sql import functions as F

from src.quality.rules import rule_is_not_null, rule_matches_regex, QualityRule, build_composite_rule_expression, extract_failed_rule_names
from src.quality.quarantine import apply_quality_rules

def test_rule_is_not_null():
    """Test generating a NOT NULL rule."""
    rule = rule_is_not_null("customer_id")
    assert rule.name == "customer_id_not_null"
    assert rule.description == "Ensures column 'customer_id' contains no null values"
    assert rule.is_fatal is True
    # rule.expression is a Column, we can't assert its string value easily, but we can verify it's a Column

def test_rule_matches_regex():
    """Test generating a regex rule."""
    rule = rule_matches_regex("status", "^(ACTIVE|PENDING)$")
    assert rule.name == "status_matches_regex"
    assert rule.description == "Ensures column 'status' matches pattern '^(ACTIVE|PENDING)$'"
    assert rule.is_fatal is True

def test_quarantine_manager_split(spark):
    """Test splitting valid and invalid records using apply_quality_rules."""
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
    
    rules = [
        rule_is_not_null("id"),
        rule_is_not_null("email")
    ]
    
    # We want valid records to have BOTH id and email
    valid_df, quarantine_df = apply_quality_rules(
        df,
        rules=rules,
        quarantine_reason_col="_quarantine_failed_rules"
    )
    
    valid_records = valid_df.collect()
    quarantine_records = quarantine_df.collect()
    
    assert len(valid_records) == 1
    assert valid_records[0].id == 1
    
    assert len(quarantine_records) == 2
    # Verify the quarantine column was added
    assert "_quarantine_failed_rules" in quarantine_df.columns


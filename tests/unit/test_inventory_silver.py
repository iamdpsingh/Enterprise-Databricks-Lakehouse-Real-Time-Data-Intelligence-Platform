import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from src.pipelines.inventory.silver_processing import process_inventory_silver

@pytest.fixture
def inventory_bronze_schema():
    return StructType([
        StructField("product_id", StringType(), True),
        StructField("warehouse_id", StringType(), True),
        StructField("stock_level", IntegerType(), True),
        StructField("updated_at", StringType(), True)
    ])

def test_process_inventory_silver_quarantine(spark: SparkSession, tmp_path, inventory_bronze_schema):
    """
    Test that invalid inventory records (negative stock, missing IDs) are quarantined.
    """
    bronze_path = f"{tmp_path}/bronze"
    silver_path = f"{tmp_path}/silver"
    quarantine_path = f"{tmp_path}/quarantine"
    
    # Create sample bronze data with one valid and two invalid records
    bronze_data = [
        ("prod1", "wh1", 100, "2024-01-01T10:00:00Z"), # Valid
        (None, "wh1", 50, "2024-01-01T10:00:00Z"),     # Invalid: missing product_id
        ("prod2", "wh2", -10, "2024-01-01T10:00:00Z")  # Invalid: negative stock
    ]
    
    bronze_df = spark.createDataFrame(bronze_data, inventory_bronze_schema)
    bronze_df.write.format("delta").save(bronze_path)
    
    # Create empty silver delta table schema (for SCD2 target)
    silver_schema = StructType([
        StructField("product_id", StringType(), True),
        StructField("warehouse_id", StringType(), True),
        StructField("stock_level", IntegerType(), True),
        StructField("updated_at", StringType(), True),
        StructField("is_current", StringType(), True),
        StructField("valid_from", StringType(), True),
        StructField("valid_to", StringType(), True)
    ])
    spark.createDataFrame([], silver_schema).write.format("delta").save(silver_path)
    
    spark.sql("DROP TABLE IF EXISTS bronze_inv")
    spark.sql("DROP TABLE IF EXISTS silver_inv")
    spark.sql(f"CREATE TABLE bronze_inv USING DELTA LOCATION '{bronze_path}'")
    spark.sql(f"CREATE TABLE silver_inv USING DELTA LOCATION '{silver_path}'")
    
    # Create empty quarantine delta table schema
    quarantine_schema = StructType(inventory_bronze_schema.fields + [StructField("quarantine_reason", StringType(), True)])
    spark.createDataFrame([], quarantine_schema).write.format("delta").save(quarantine_path)
    spark.sql("DROP TABLE IF EXISTS quarantine_inv")
    spark.sql(f"CREATE TABLE quarantine_inv USING DELTA LOCATION '{quarantine_path}'")
    
    process_inventory_silver(spark, "bronze_inv", "silver_inv", "quarantine_inv")
    
    quarantine_df = spark.read.format("delta").load(quarantine_path)
    assert quarantine_df.count() == 2
    
    invalid_reasons = quarantine_df.select("quarantine_reason").rdd.flatMap(lambda x: x).collect()
    assert any("product_id_not_null" in reason for reason in invalid_reasons if reason)
    assert any("stock_level_non_negative" in reason for reason in invalid_reasons if reason)

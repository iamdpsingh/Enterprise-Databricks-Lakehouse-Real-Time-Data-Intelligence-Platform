import pytest
from pyspark.sql import SparkSession
from pyspark.sql import Row

from src.pipelines.orders.silver_processing import process_orders_silver
from delta.tables import DeltaTable

def test_process_orders_silver(spark: SparkSession, tmp_path):
    # Setup paths
    bronze_path = str(tmp_path / "bronze_orders")
    silver_path = str(tmp_path / "silver_orders")
    quarantine_path = str(tmp_path / "quarantine_orders")
    
    # 1. Create source (Bronze) data with some bad records
    bronze_data = [
        Row(order_id="1", customer_id="C1", total_amount=100.0, created_at="2024-01-01T10:00:00Z"),
        Row(order_id="2", customer_id="C2", total_amount=-50.0, created_at="2024-01-01T11:00:00Z"), # Bad: total_amount < 0
        Row(order_id=None, customer_id="C3", total_amount=200.0, created_at="2024-01-01T12:00:00Z"), # Bad: order_id is null
        Row(order_id="4", customer_id="C4", total_amount=150.0, created_at="2024-01-01T13:00:00Z"),
    ]
    
    bronze_df = spark.createDataFrame(bronze_data)
    bronze_df.write.format("delta").save(bronze_path)
    
    # Register as tables for the function to read/write using spark.read.table
    spark.sql(f"CREATE TABLE bronze_orders USING DELTA LOCATION '{bronze_path}'")
    
    # 2. Create target (Silver) table (empty initially)
    silver_schema = bronze_df.schema
    spark.createDataFrame([], schema=silver_schema).write.format("delta").save(silver_path)
    spark.sql(f"CREATE TABLE silver_orders USING DELTA LOCATION '{silver_path}'")
    
    # Create quarantine table (empty initially)
    spark.createDataFrame([], schema=silver_schema).write.format("delta").save(quarantine_path)
    spark.sql(f"CREATE TABLE quarantine_orders USING DELTA LOCATION '{quarantine_path}'")
    
    # 3. Run the processing function
    process_orders_silver(spark, "bronze_orders", "silver_orders", "quarantine_orders")
    
    # 4. Assertions
    silver_df = spark.read.format("delta").load(silver_path)
    quarantine_df = spark.read.format("delta").load(quarantine_path)
    
    # 2 good records should be in silver
    assert silver_df.count() == 2
    valid_order_ids = [row.order_id for row in silver_df.collect()]
    assert "1" in valid_order_ids
    assert "4" in valid_order_ids
    
    # 2 bad records should be in quarantine
    assert quarantine_df.count() == 2
    quarantined_customers = [row.customer_id for row in quarantine_df.collect()]
    assert "C2" in quarantined_customers # failed total_amount
    assert "C3" in quarantined_customers # failed order_id
    
    # Teardown
    spark.sql("DROP TABLE IF EXISTS bronze_orders")
    spark.sql("DROP TABLE IF EXISTS silver_orders")
    spark.sql("DROP TABLE IF EXISTS quarantine_orders")

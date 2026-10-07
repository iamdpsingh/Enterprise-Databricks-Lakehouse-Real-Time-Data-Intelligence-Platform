import pytest
from pyspark.sql import SparkSession
from pyspark.sql import Row

from src.pipelines.orders.gold_aggregation import aggregate_orders_gold

def test_aggregate_orders_gold(spark: SparkSession, tmp_path):
    # Setup paths
    silver_path = str(tmp_path / "silver_orders")
    gold_path = str(tmp_path / "gold_metrics")
    
    # 1. Create source (Silver) data
    silver_data = [
        Row(order_id="1", customer_id="C1", total_amount=100.0, created_at="2024-01-01T10:00:00Z"),
        Row(order_id="2", customer_id="C1", total_amount=50.0, created_at="2024-01-01T15:00:00Z"),
        Row(order_id="3", customer_id="C2", total_amount=200.0, created_at="2024-01-02T10:00:00Z"),
    ]
    
    silver_df = spark.createDataFrame(silver_data)
    silver_df.write.format("delta").save(silver_path)
    spark.sql(f"CREATE TABLE silver_orders_test USING DELTA LOCATION '{silver_path}'")
    
    # Register empty gold table location
    spark.sql(f"CREATE TABLE gold_metrics_test USING DELTA LOCATION '{gold_path}'")
    
    # 3. Run the processing function
    aggregate_orders_gold(spark, "silver_orders_test", "gold_metrics_test")
    
    # 4. Assertions
    gold_df = spark.read.format("delta").load(gold_path)
    
    # Should be grouped by 2 distinct dates
    assert gold_df.count() == 2
    
    results = {str(row.order_date): row for row in gold_df.collect()}
    
    # Check 2024-01-01 aggregations
    assert results["2024-01-01"].daily_revenue == 150.0
    assert results["2024-01-01"].daily_order_count == 2
    assert results["2024-01-01"].unique_customers == 1
    
    # Check 2024-01-02 aggregations
    assert results["2024-01-02"].daily_revenue == 200.0
    assert results["2024-01-02"].daily_order_count == 1
    assert results["2024-01-02"].unique_customers == 1
    
    # Teardown
    spark.sql("DROP TABLE IF EXISTS silver_orders_test")
    spark.sql("DROP TABLE IF EXISTS gold_metrics_test")

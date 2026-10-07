import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType

from src.pipelines.inventory.gold_aggregation import aggregate_inventory_gold

@pytest.fixture
def inventory_silver_schema():
    return StructType([
        StructField("product_id", StringType(), True),
        StructField("warehouse_id", StringType(), True),
        StructField("stock_level", IntegerType(), True),
        StructField("is_current", BooleanType(), True)
    ])

def test_aggregate_inventory_gold(spark: SparkSession, tmp_path, inventory_silver_schema):
    """
    Test that Gold aggregation correctly filters out historical SCD2 records and 
    aggregates stock by warehouse.
    """
    silver_path = f"{tmp_path}/silver"
    gold_path = f"{tmp_path}/gold"
    
    silver_data = [
        ("prod1", "wh1", 100, True),  # Active
        ("prod1", "wh1", 80, False),  # Historical (ignore)
        ("prod2", "wh1", 50, True),   # Active
        ("prod3", "wh2", 200, True),  # Active
    ]
    
    silver_df = spark.createDataFrame(silver_data, inventory_silver_schema)
    silver_df.write.format("delta").save(silver_path)
    
    spark.sql(f"CREATE TABLE silver_inv_gold_test USING DELTA LOCATION '{silver_path}'")
    
    aggregate_inventory_gold(spark, "silver_inv_gold_test", f"delta.`{gold_path}`")
    
    gold_df = spark.read.format("delta").load(gold_path)
    
    # Warehouse 1: 100 + 50 = 150 stock, 2 products
    wh1 = gold_df.filter("warehouse_id = 'wh1'").collect()[0]
    assert wh1.total_stock_level == 150
    assert wh1.unique_products_in_stock == 2
    
    # Warehouse 2: 200 stock, 1 product
    wh2 = gold_df.filter("warehouse_id = 'wh2'").collect()[0]
    assert wh2.total_stock_level == 200
    assert wh2.unique_products_in_stock == 1

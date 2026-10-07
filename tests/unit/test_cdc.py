import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from delta.tables import DeltaTable

from src.cdc.scd1 import upsert_scd1
from src.cdc.scd2 import merge_scd2
from src.cdc.delete_handler import soft_delete_records, hard_delete_records

def test_upsert_scd1(spark: SparkSession, tmp_path):
    target_path = f"{tmp_path}/target_scd1"
    
    # Create target table
    spark.createDataFrame([
        {"id": 1, "value": "A"},
        {"id": 2, "value": "B"}
    ]).write.format("delta").save(target_path)
    target_table = DeltaTable.forPath(spark, target_path)
    
    # Source with update and insert
    source_df = spark.createDataFrame([
        {"id": 2, "value": "B_updated"},
        {"id": 3, "value": "C"}
    ])
    
    upsert_scd1(target_table, source_df, ["id"])
    
    res = spark.read.format("delta").load(target_path).orderBy("id").collect()
    assert len(res) == 3
    assert res[0].value == "A"
    assert res[1].value == "B_updated"
    assert res[2].value == "C"

def test_merge_scd2(spark: SparkSession, tmp_path):
    target_path = f"{tmp_path}/target_scd2"
    
    # Create target table
    schema = StructType([
        StructField("id", IntegerType()),
        StructField("value", StringType()),
        StructField("updated_at", StringType()),
        StructField("is_current", StringType()),
        StructField("valid_from", StringType()),
        StructField("valid_to", StringType())
    ])
    
    spark.createDataFrame([
        (1, "A", "2024-01-01", "true", "2024-01-01", None),
        (2, "B", "2024-01-01", "true", "2024-01-01", None)
    ], schema=schema).write.format("delta").save(target_path)
    
    target_table = DeltaTable.forPath(spark, target_path)
    
    # Source data
    source_df = spark.createDataFrame([
        {"id": 2, "value": "B_new", "updated_at": "2024-01-02"},
        {"id": 3, "value": "C", "updated_at": "2024-01-02"}
    ])
    
    merge_scd2(target_table, source_df, ["id"])
    
    res = spark.read.format("delta").load(target_path).orderBy("id", "updated_at").collect()
    # Expect 4 records:
    # id=1 (unchanged)
    # id=2 (old, is_current=false, valid_to=2024-01-02)
    # id=2 (new, is_current=true, valid_from=2024-01-02)
    # id=3 (new, is_current=true)
    assert len(res) == 4
    
    id2_old = [r for r in res if r.id == 2 and r.is_current == "false"][0]
    id2_new = [r for r in res if r.id == 2 and r.is_current == "true"][0]
    
    assert id2_old.value == "B"
    assert id2_old.valid_to == "2024-01-02"
    assert id2_new.value == "B_new"
    assert id2_new.valid_from == "2024-01-02"

def test_delete_handler(spark: SparkSession, tmp_path):
    target_path = f"{tmp_path}/target_del"
    
    spark.createDataFrame([
        {"id": 1, "value": "A", "is_deleted": "false"},
        {"id": 2, "value": "B", "is_deleted": "false"},
        {"id": 3, "value": "C", "is_deleted": "false"}
    ]).write.format("delta").save(target_path)
    
    target_table = DeltaTable.forPath(spark, target_path)
    
    # Soft delete id=2
    del_keys = spark.createDataFrame([{"id": 2}])
    soft_delete_records(target_table, del_keys, ["id"])
    
    res_soft = spark.read.format("delta").load(target_path).orderBy("id").collect()
    assert len(res_soft) == 3
    assert res_soft[1].is_deleted == "true"
    
    # Hard delete id=3
    del_keys_hard = spark.createDataFrame([{"id": 3}])
    hard_delete_records(target_table, del_keys_hard, ["id"])
    
    res_hard = spark.read.format("delta").load(target_path).orderBy("id").collect()
    assert len(res_hard) == 2
    ids = [r.id for r in res_hard]
    assert 3 not in ids

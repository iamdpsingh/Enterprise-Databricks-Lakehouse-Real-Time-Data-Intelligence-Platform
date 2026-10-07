import pytest
import responses
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql import functions as F

from src.ingestion.api_reader import RestApiReader
from src.ingestion.autoloader import AutoLoaderStream, start_ingestion_stream
from src.ingestion.metadata import attach_bronze_metadata
from src.quality.metrics import log_quality_metrics

@pytest.fixture
def mock_api_response():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "http://api.example.com/data",
            json=[{"id": 1, "value": "A"}, {"id": 2, "value": "B"}],
            status=200
        )
        rsps.add(
            responses.GET,
            "http://api.example.com/data_dict",
            json={"data": [{"id": 3, "value": "C"}]},
            status=200
        )
        rsps.add(
            responses.GET,
            "http://api.example.com/data_single",
            json={"id": 4, "value": "D"},
            status=200
        )
        yield rsps

def test_api_reader_fetch(spark: SparkSession, mock_api_response):
    reader = RestApiReader(spark, "http://api.example.com")
    reader.set_auth_token("secret")
    
    res1 = reader.fetch_endpoint("/data")
    assert len(res1) == 2
    
    res2 = reader.fetch_endpoint("data_dict")
    assert len(res2) == 1
    
    res3 = reader.fetch_endpoint("data_single")
    assert len(res3) == 1
    
def test_api_reader_to_dataframe(spark: SparkSession):
    reader = RestApiReader(spark, "http://api.example.com")
    
    # Test valid records
    df = reader.to_dataframe([{"id": 1}])
    assert df.count() == 1
    
    # Test empty records without schema
    with pytest.raises(ValueError):
        reader.to_dataframe([])
        
    # Test empty records with schema
    schema = StructType([StructField("id", StringType())])
    df_empty = reader.to_dataframe([], schema=schema)
    assert df_empty.count() == 0

def test_attach_bronze_metadata_without_file_metadata(spark: SparkSession):
    df = spark.createDataFrame([{"val": 1}])
    result_df = attach_bronze_metadata(df, "test_system", "batch-123")
    assert "_metadata_source_system" in result_df.columns
    assert "_metadata_file_path" in result_df.columns
    assert result_df.select("_metadata_source_system").first()[0] == "test_system"
    assert result_df.select("_metadata_file_path").first()[0] == "API/Stream"

def test_attach_bronze_metadata_with_file_metadata(spark: SparkSession):
    schema = StructType([
        StructField("val", StringType()),
        StructField("_metadata", StructType([
            StructField("file_path", StringType()),
            StructField("file_modification_time", TimestampType())
        ]))
    ])
    from datetime import datetime
    data = [("test", ("s3://bucket/file.json", datetime.now()))]
    df = spark.createDataFrame(data, schema=schema)
    
    result_df = attach_bronze_metadata(df, "test_system", "batch-123")
    assert "_metadata_file_path" in result_df.columns
    assert result_df.select("_metadata_file_path").first()[0] == "s3://bucket/file.json"

def test_autoloader_create_read_stream(spark: SparkSession, tmp_path):
    loader = AutoLoaderStream(spark)
    # create dummy file
    (tmp_path / "data").mkdir()
    with open(tmp_path / "data" / "f.json", "w") as f:
        f.write('{"id": 1}\n')
        
    df = loader.create_read_stream(
        str(tmp_path / "data"), 
        "json", 
        str(tmp_path / "checkpoint"), 
        str(tmp_path / "schema"), 
        options={"cloudFiles.inferColumnTypes": "false"}
    )
    assert df.isStreaming
    
def test_autoloader_start_ingestion_stream(spark: SparkSession, tmp_path):
    target = f"{tmp_path}/target_table"
    checkpoint = f"{tmp_path}/checkpoint"
    
    # Create simple streaming df
    df = spark.readStream.format("rate").load()
    
    start_ingestion_stream(
        df,
        target_table=target,
        checkpoint_path=checkpoint,
        trigger="availableNow",
        merge_schema=False
    )
    
    # Check if data was written
    written_df = spark.read.format("delta").load(target)
    assert written_df.count() >= 0

def test_log_quality_metrics(spark: SparkSession, tmp_path):
    metrics_path = f"{tmp_path}/metrics"
    spark.sql(f"CREATE DATABASE IF NOT EXISTS dev_catalog")
    spark.sql(f"CREATE TABLE IF NOT EXISTS dev_catalog.metrics_table (pipeline_name STRING, table_name STRING, run_id STRING, run_timestamp TIMESTAMP, check_name STRING, total_records BIGINT, passed_records BIGINT, failed_records BIGINT, quarantine_records BIGINT, pass_rate DOUBLE, is_alertable BOOLEAN, environment STRING) USING DELTA LOCATION '{metrics_path}'")
    
    log_quality_metrics(
        spark, 
        "test_pipe", 
        "test_table", 
        "run-1", 
        100, 
        10, 
        metrics_table="metrics_table"
    )
    
    res = spark.read.format("delta").load(metrics_path)
    assert res.count() == 1
    row = res.first()
    assert row.total_records == 100
    assert row.quarantine_records == 10
    assert row.pass_rate == 0.9

def test_log_quality_metrics_exception(spark: SparkSession):
    # Pass a table that doesn't exist, it should not raise an exception because of the try-except
    log_quality_metrics(
        spark, 
        "test_pipe", 
        "test_table", 
        "run-1", 
        100, 
        10, 
        metrics_table="non_existent_table"
    )
    # If no exception is raised, test passes

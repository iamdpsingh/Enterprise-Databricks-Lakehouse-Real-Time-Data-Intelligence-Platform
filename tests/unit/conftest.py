import logging
import pytest
from pyspark.sql import SparkSession

# Silence excessive py4j logging during tests
logging.getLogger("py4j").setLevel(logging.ERROR)

@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """
    Creates a local SparkSession for unit testing.
    Scope is 'session' so it's created once and reused across all tests,
    significantly speeding up test execution.
    """
    import delta
    
    builder = (
        SparkSession.builder
        .master("local[2]")
        .appName("lakehouse-unit-tests")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    
    spark_session = delta.configure_spark_with_delta_pip(builder).getOrCreate()
    
    yield spark_session
    
    spark_session.stop()

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
    spark_session = (
        SparkSession.builder
        .master("local[2]")
        .appName("lakehouse-unit-tests")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    
    yield spark_session
    
    spark_session.stop()

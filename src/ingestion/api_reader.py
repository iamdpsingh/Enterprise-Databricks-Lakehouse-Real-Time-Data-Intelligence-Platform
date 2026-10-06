import json
from typing import Dict, Any, List

import requests
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

from src.utilities.logger import logger
from src.utilities.retry import with_retry

class RestApiReader:
    """Utility class for fetching data from REST APIs and converting to Spark DataFrames."""
    
    def __init__(self, spark: SparkSession, base_url: str):
        self.spark = spark
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def set_auth_token(self, token: str) -> None:
        """Sets the Bearer token for authentication."""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    @with_retry(max_attempts=3, min_wait_seconds=2, max_wait_seconds=10)
    def fetch_endpoint(self, endpoint: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Fetches data from a specific API endpoint. Uses retry logic.
        
        Args:
            endpoint: The API endpoint path (e.g., '/api/v1/customers').
            params: Query parameters.
            
        Returns:
            A list of dictionary objects representing the JSON response.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"Fetching data from API: {url}")
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Simple assumption: API returns a list of records. 
        # For complex APIs, this parsing logic would be more sophisticated or passed as a callback.
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "data" in data:
            return data["data"]
        else:
            return [data]

    def to_dataframe(self, records: List[Dict[str, Any]], schema: StructType = None) -> DataFrame:
        """
        Converts a list of dictionary records to a Spark DataFrame.
        
        Args:
            records: The list of dicts.
            schema: Optional explicit Spark schema. If None, Spark will infer it.
            
        Returns:
            A PySpark DataFrame.
        """
        if not records:
            logger.warning("No records to convert to DataFrame.")
            if schema:
                return self.spark.createDataFrame([], schema)
            else:
                raise ValueError("Cannot infer schema from empty record list without explicit schema.")
                
        # For large data volumes, writing to a temp JSON file and reading via Spark
        # is more efficient than createDataFrame, but for typical API payloads this is fine.
        return self.spark.createDataFrame(records, schema)

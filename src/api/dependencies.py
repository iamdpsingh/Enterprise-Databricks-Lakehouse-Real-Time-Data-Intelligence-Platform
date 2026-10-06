from typing import Any, Generator
from databricks.sql import connect

from src.utilities.config import ConfigLoader
from src.utilities.logger import logger

config = ConfigLoader()

def get_databricks_connection() -> Generator[Any, None, None]:
    """
    FastAPI dependency that yields a Databricks SQL connection and ensures it's closed.
    Uses environment variables for authentication.
    """
    # These would typically come from Secret Manager via config
    server_hostname = config.get("DATABRICKS_SERVER_HOSTNAME", "dummy-hostname")
    http_path = config.get("DATABRICKS_HTTP_PATH", "dummy-http-path")
    access_token = config.get("DATABRICKS_TOKEN", "dummy-token")
    
    logger.debug("Opening Databricks SQL Connection")
    connection = None
    try:
        connection = connect(
            server_hostname=server_hostname,
            http_path=http_path,
            access_token=access_token
        )
        yield connection
    finally:
        if connection:
            logger.debug("Closing Databricks SQL Connection")
            connection.close()

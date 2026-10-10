import os
from databricks import sql
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DATABRICKS_HOST")
http_path = os.getenv("NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH") or os.getenv("DATABRICKS_SQL_HTTP_PATH")
token = os.getenv("DATABRICKS_TOKEN") or os.getenv("NEXT_PUBLIC_DATABRICKS_API_TOKEN")

print(f"Connecting to: {host} {http_path}")

try:
    with sql.connect(server_hostname=host.replace("https://", ""),
                     http_path=http_path,
                     access_token=token) as connection:
        with connection.cursor() as cursor:
            print("Executing query...")
            cursor.execute("""
                SELECT 
                  (SELECT COUNT(*) FROM prod_catalog.ethereum.bronze) as eth_count,
                  (SELECT COUNT(*) FROM prod_catalog.github.bronze) as gh_count,
                  (SELECT COUNT(*) FROM prod_catalog.overture.bronze) as ov_count
            """)
            result = cursor.fetchall()
            print("Result:", result)
except Exception as e:
    print("Error:", e)

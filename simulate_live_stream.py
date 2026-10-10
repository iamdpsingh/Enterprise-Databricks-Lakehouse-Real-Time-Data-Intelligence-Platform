import os
import time
import random
import uuid
from datetime import datetime
from dotenv import load_dotenv
from databricks import sql

# Load environment variables from .env
load_dotenv()

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "").replace("https://", "").rstrip("/")
DATABRICKS_HTTP_PATH = os.getenv("NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

if not all([DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN]):
    print("❌ ERROR: Missing Databricks credentials in .env file!")
    print("Make sure DATABRICKS_HOST, NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH, and DATABRICKS_TOKEN are set.")
    exit(1)

def get_connection():
    return sql.connect(
        server_hostname=DATABRICKS_HOST,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN
    )

def insert_fake_data(cursor):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # 1. ETHEREUM: Random gas and value
    eth_hash = f"0x{uuid.uuid4().hex}"
    gas = str(random.randint(21000, 500000))
    value = str(random.randint(0, 1000000000000000000))
    cursor.execute(f"""
        INSERT INTO prod_catalog.ethereum.bronze (hash, gas, value, block_timestamp)
        VALUES ('{eth_hash}', '{gas}', '{value}', '{now}')
    """)

    # 2. GITHUB: Random event types
    gh_id = str(random.randint(10000000000, 99999999999))
    gh_type = random.choice(["PushEvent", "PullRequestEvent", "IssueCommentEvent", "CreateEvent"])
    repo_name = random.choice(["facebook/react", "vercel/next.js", "torvalds/linux", "databricks/databricks-sql-nodejs"])
    cursor.execute(f"""
        INSERT INTO prod_catalog.github.bronze (id, type, repo_name, created_at)
        VALUES ('{gh_id}', '{gh_type}', '{repo_name}', '{now}')
    """)

    # 3. OVERTURE MAPS: Random lat/lon
    ov_id = f"poi_{uuid.uuid4().hex[:10]}"
    category = random.choice(["Restaurant", "Coffee Shop", "Hospital", "School", "Gas Station"])
    lat = round(random.uniform(-90.0, 90.0), 6)
    lon = round(random.uniform(-180.0, 180.0), 6)
    cursor.execute(f"""
        INSERT INTO prod_catalog.overture.bronze (id, category, lat, lon)
        VALUES ('{ov_id}', '{category}', {lat}, {lon})
    """)

print("🚀 Starting Multi-Dataset Live Stream Simulation...")
print(f"🔗 Connecting to Databricks Host: {DATABRICKS_HOST}")

try:
    connection = get_connection()
    cursor = connection.cursor()
    print("✅ Connected successfully! Beginning data ingestion loop (Press CTRL+C to stop).")
    
    insertions = 0
    while True:
        insert_fake_data(cursor)
        insertions += 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ Inserted Batch #{insertions} (Eth, GitHub, Overture)")
        
        # Sleep for 1 to 3 seconds to simulate variable streaming rate
        time.sleep(random.uniform(1.0, 3.0))

except KeyboardInterrupt:
    print("\n🛑 Simulation stopped by user.")
except Exception as e:
    print(f"\n❌ An error occurred: {e}")
finally:
    try:
        cursor.close()
        connection.close()
    except:
        pass

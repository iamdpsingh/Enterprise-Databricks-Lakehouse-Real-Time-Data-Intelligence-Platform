import os
import json
import uuid
import time
import random
from datetime import datetime, timezone
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
import io
import sys
import requests

# Ensure src module is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.utilities.logger import logger

# Load Databricks credentials from .env
load_dotenv()
HOST = os.getenv("DATABRICKS_HOST")
TOKEN = os.getenv("DATABRICKS_TOKEN")

if not HOST or not TOKEN:
    logger.error("Missing DATABRICKS_HOST or DATABRICKS_TOKEN in .env")
    exit(1)

# Initialize the Databricks SDK
w = WorkspaceClient(host=HOST, token=TOKEN)
logger.info(f"Successfully authenticated to Databricks Workspace: {HOST}")

def fetch_ethereum_data():
    try:
        # Fetch real Ethereum price & volume from Binance API
        r = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT', timeout=5).json()
        return {
            "hash": f"eth_price_update_{uuid.uuid4().hex[:8]}",
            "gas": str(int(float(r.get('lastPrice', random.randint(21000, 500000))))), # using price as proxy for 'gas' in our schema
            "value": str(int(float(r.get('volume', random.randint(0, 1000000))))), # using 24h volume as proxy for 'value'
            "block_timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.warning(f"Crypto API failed, falling back to local generator: {e}")
        return {
            "hash": f"0x{uuid.uuid4().hex}",
            "gas": str(random.randint(21000, 500000)),
            "value": str(random.randint(0, 1000000000000000000)),
            "block_timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }

def fetch_github_data():
    try:
        # Fetch real recent GitHub events
        r = requests.get('https://api.github.com/events', timeout=5).json()
        if isinstance(r, list) and len(r) > 0:
            event = r[0] # grab the most recent event
            return {
                "id": str(event.get("id", random.randint(10000000000, 99999999999))),
                "type": event.get("type", "UnknownEvent"),
                "repo_name": event.get("repo", {}).get("name", "unknown/repo"),
                "created_at": event.get("created_at", datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
            }
    except Exception as e:
        logger.warning(f"GitHub API failed (possibly rate limited), falling back to local generator: {e}")
        
    return {
        "id": str(random.randint(10000000000, 99999999999)),
        "type": random.choice(["PushEvent", "PullRequestEvent", "IssueCommentEvent", "CreateEvent"]),
        "repo_name": random.choice(["facebook/react", "vercel/next.js", "torvalds/linux", "apache/spark"]),
        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

def fetch_overture_data():
    try:
        # Fetch real International Space Station location
        r = requests.get('http://api.open-notify.org/iss-now.json', timeout=5).json()
        pos = r.get('iss_position', {})
        
        # Inject occasional malformed data (10% chance) to trigger the Dead Letter Queue
        if random.random() < 0.10:
            lat = 95.0 # Invalid latitude to trigger DLQ
        else:
            lat = float(pos.get('latitude', random.uniform(30.0, 90.0)))
            
        return {
            "id": f"iss_{r.get('timestamp', uuid.uuid4().hex[:10])}",
            "name": "International Space Station",
            "category": "satellite",
            "latitude": lat,
            "longitude": float(pos.get('longitude', random.uniform(-125.0, -70.0))),
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.warning(f"ISS API failed, falling back to local generator: {e}")
        lat = random.uniform(30.0, 95.0)
        lon = random.uniform(-125.0, -70.0)
        return {
            "id": f"poi_{uuid.uuid4().hex[:10]}",
            "name": random.choice(["Central Park", "Eiffel Tower", "Golden Gate Bridge", "Louvre Museum", "Unknown Location"]),
            "category": random.choice(["park", "landmark", "museum", "restaurant"]),
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        }

logger.info("Starting API -> Databricks Unity Catalog Volume pipeline...")

checkpoint_file = "logs/checkpoint.json"
insertions = 0

# Resume from checkpoint if it exists
if os.path.exists(checkpoint_file):
    try:
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
            insertions = data.get("last_batch_id", 0)
            logger.info(f"Resuming pipeline from Batch #{insertions}...")
    except Exception as e:
        logger.warning(f"Could not read checkpoint file, starting fresh: {e}")

while True:
    try:
        eth_payload = fetch_ethereum_data()
        gh_payload = fetch_github_data()
        ov_payload = fetch_overture_data()

        date_partition = datetime.now(timezone.utc).strftime('%Y/%m/%d')
        
        # Databricks Volume Paths
        eth_path = f"/Volumes/prod_catalog/ethereum/raw_landing/{date_partition}/eth_{uuid.uuid4().hex[:8]}.json"
        gh_path = f"/Volumes/prod_catalog/github/raw_landing/{date_partition}/gh_{uuid.uuid4().hex[:8]}.json"
        ov_path = f"/Volumes/prod_catalog/overture/raw_landing/{date_partition}/ov_{uuid.uuid4().hex[:8]}.json"

        # Upload using Databricks SDK (bypasses GCP IAM completely)
        w.files.upload(eth_path, io.BytesIO(json.dumps(eth_payload).encode('utf-8')))
        w.files.upload(gh_path, io.BytesIO(json.dumps(gh_payload).encode('utf-8')))
        w.files.upload(ov_path, io.BytesIO(json.dumps(ov_payload).encode('utf-8')))

        insertions += 1
        
        # Save checkpoint state
        with open(checkpoint_file, 'w') as f:
            json.dump({"last_batch_id": insertions, "timestamp": datetime.now(timezone.utc).isoformat()}, f)
            
        logger.info(f"Uploaded Batch #{insertions} to Unity Catalog Volumes")

        time.sleep(3.0)

    except KeyboardInterrupt:
        logger.warning("Ingestion stopped by user.")
        break
    except Exception as e:
        logger.error(f"Error during Databricks Volume upload: {e}")
        time.sleep(5)

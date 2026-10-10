import os
import json
import uuid
import time
import random
from datetime import datetime
from google.cloud import storage
from dotenv import load_dotenv

# Load GCP credentials from .env
load_dotenv()
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GCP_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Ensure environment variables are set
if not GCP_PROJECT or not GCP_CREDS:
    print("❌ ERROR: Missing GCP credentials in .env file (GOOGLE_CLOUD_PROJECT or GOOGLE_APPLICATION_CREDENTIALS).")
    exit(1)

# Set the environment variable explicitly for the python SDK
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_CREDS

# Define the bucket name (must exist in your GCP project)
BUCKET_NAME = f"{GCP_PROJECT}-raw-landing-zone"

try:
    client = storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(BUCKET_NAME)
    # Check if bucket exists, if not, attempt to create it (requires proper permissions)
    if not bucket.exists():
        print(f"🪣 Bucket {BUCKET_NAME} not found. Creating...")
        bucket = client.create_bucket(BUCKET_NAME, location="US")
    print(f"✅ Successfully connected to GCP Bucket: {BUCKET_NAME}")
except Exception as e:
    print(f"❌ Failed to connect to GCP. Is your Service Account JSON valid? Error: {e}")
    exit(1)

def fetch_ethereum_data():
    """Simulate fetching raw data from Ethereum RPC/Web3 API"""
    return {
        "hash": f"0x{uuid.uuid4().hex}",
        "gas": str(random.randint(21000, 500000)),
        "value": str(random.randint(0, 1000000000000000000)),
        "block_timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

def fetch_github_data():
    """Simulate fetching raw data from GitHub Events API"""
    return {
        "id": str(random.randint(10000000000, 99999999999)),
        "type": random.choice(["PushEvent", "PullRequestEvent", "IssueCommentEvent", "CreateEvent"]),
        "repo_name": random.choice(["facebook/react", "vercel/next.js", "torvalds/linux", "apache/spark"]),
        "created_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

print("🚀 Starting real API -> GCP Cloud Storage pipeline...")
insertions = 0

while True:
    try:
        # 1. Fetch data
        eth_payload = fetch_ethereum_data()
        gh_payload = fetch_github_data()

        # 2. Define GCS object paths (partitioned by date)
        date_partition = datetime.utcnow().strftime('%Y/%m/%d')
        eth_blob_name = f"ethereum/raw/{date_partition}/eth_{uuid.uuid4().hex[:8]}.json"
        gh_blob_name = f"github/raw/{date_partition}/gh_{uuid.uuid4().hex[:8]}.json"

        # 3. Upload Ethereum to GCP
        eth_blob = bucket.blob(eth_blob_name)
        eth_blob.upload_from_string(json.dumps(eth_payload), content_type="application/json")

        # 4. Upload GitHub to GCP
        gh_blob = bucket.blob(gh_blob_name)
        gh_blob.upload_from_string(json.dumps(gh_payload), content_type="application/json")

        insertions += 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ☁️ Uploaded Batch #{insertions} to GCP GCS Bucket -> {BUCKET_NAME}")

        # Sleep to simulate interval API polling
        time.sleep(3.0)

    except KeyboardInterrupt:
        print("\n🛑 GCP Ingestion stopped by user.")
        break
    except Exception as e:
        print(f"\n❌ Error during GCP upload: {e}")
        time.sleep(5) # Backoff before retrying

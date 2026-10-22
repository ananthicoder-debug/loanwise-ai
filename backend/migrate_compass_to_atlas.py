"""
LoanWise AI — Sync MongoDB Compass data to MongoDB Atlas.
Run this script to upload all your local collections to Atlas for Render.
"""
import sys, os
from pymongo import MongoClient

LOCAL_URI = "mongodb://127.0.0.1:27017"
ATLAS_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://ananthavalliuofficial_db_user:nraXeFPEfhtvTuxC@cluster0.ckt9xiq.mongodb.net/loan_ai_system?retryWrites=true&w=majority&appName=Cluster0"
)
DB_NAME = "loan_ai_system"

def sync():
    print(f"[1/3] Connecting to Local MongoDB Compass at {LOCAL_URI}...")
    try:
        local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=3000)
        local_client.admin.command("ping")
        local_db = local_client[DB_NAME]
        cols = local_db.list_collection_names()
        print(f"      Found {len(cols)} collections in local '{DB_NAME}'.")
    except Exception as e:
        print(f"      ERROR connecting to local MongoDB: {e}")
        return

    print(f"\n[2/3] Connecting to MongoDB Atlas...")
    try:
        atlas_client = MongoClient(
            ATLAS_URI,
            serverSelectionTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=True,
            w="majority"
        )
        atlas_client.admin.command("ping")
        atlas_db = atlas_client[DB_NAME]
        print("      Atlas connection SUCCESSFUL!")
    except Exception as e:
        print(f"      Atlas connection FAILED: {e}")
        print("\n      ACTION NEEDED IN MONGODB ATLAS DASHBOARD:")
        print("      1. Go to https://cloud.mongodb.com")
        print("      2. In the left menu, click 'Network Access'")
        print("      3. Click 'Add IP Address' -> Choose 'Allow Access from Anywhere' (0.0.0.0/0)")
        print("      4. Wait 1 minute for Atlas to apply, then re-run this script.")
        return

    print(f"\n[3/3] Uploading data to Atlas '{DB_NAME}'...")
    total_docs = 0
    for col_name in cols:
        local_col = local_db[col_name]
        docs = list(local_col.find())
        if not docs:
            continue
        atlas_col = atlas_db[col_name]
        atlas_col.delete_many({})
        atlas_col.insert_many(docs)
        print(f"      - {col_name}: uploaded {len(docs)} document(s)")
        total_docs += len(docs)

    print(f"\n[DONE] Successfully synced {total_docs} documents from Compass to Atlas!")

if __name__ == "__main__":
    sync()

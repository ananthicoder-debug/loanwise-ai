"""Remove test lenders added during API tests, keep only the 12 real ones."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.mongodb import collections

REAL_LENDER_NAMES = [
    "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank",
    "Kotak Mahindra Bank", "IDFC FIRST Bank", "IndusInd Bank",
    "Bajaj Finance", "Tata Capital"
]
result = collections["lenders"].delete_many({"lender_name": {"$nin": REAL_LENDER_NAMES}})
print(f"Removed {result.deleted_count} extra lender(s)")
print(f"Remaining: {collections['lenders'].count_documents({})} lenders")

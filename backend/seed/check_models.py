import sys; sys.path.insert(0, '.')
from database.mongodb import collections

records = list(collections["system_metadata"].find({"key": {"$regex": "^model_performance_"}}))
print(f"Model performance records in DB: {len(records)}")
for r in records:
    print(f"  {r.get('model_name')} - accuracy={r.get('metrics',{}).get('accuracy')}")

# Also test the route is accessible
import requests
try:
    r = requests.get("http://127.0.0.1:8000/api/admin/model-performance",
                     headers={"Authorization": "Bearer test"})
    print(f"HTTP status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Connection error: {e}")

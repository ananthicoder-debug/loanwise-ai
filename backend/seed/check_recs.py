import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.mongodb import collections

recs = list(collections["recommendations"].find())
print(f"Total recommendations in DB: {len(recs)}")

apps = list(collections["loan_applications"].find())
for app in apps[:5]:
    count = collections["recommendations"].count_documents({"application_id": app["_id"]})
    print(f"  App ({app['loan_category']}): {count} recommendations (max should be 3)")

print("\nSample recommendations:")
for r in recs[:3]:
    print(f"  {r.get('product_name','?')} by {r.get('lender_name','?')}")
    print(f"  lender_website: {r.get('lender_website','NOT SET')}")
    print(f"  match_score: {r.get('match_score','?')}")
    print(f"  reason: {r.get('reason','?')[:80]}")
    print()

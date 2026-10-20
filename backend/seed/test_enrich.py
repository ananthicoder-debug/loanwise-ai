import sys; sys.path.insert(0, '.')
from database.mongodb import collections
from bson import ObjectId

print("Testing active loan enrichment...")
loans = list(collections["active_loans"].find())
print(f"Total loans: {len(loans)}")

for loan in loans:
    try:
        product = collections["loan_products"].find_one({"_id": loan["product_id"]})
        lender = collections["lenders"].find_one({"_id": product["lender_id"]}) if product else None
        pname = product["product_name"] if product else "NONE"
        lname = lender["lender_name"] if lender else "NONE"
        # Check application_id serialization
        app_id = loan.get("application_id")
        app_id_str = str(app_id) if app_id else None
        print(f"  OK: {pname} / {lname} / status={loan['status']}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()

# Test feedback serialization
print("\nTesting feedback serialization...")
fbs = list(collections["feedback"].find())
for fb in fbs:
    try:
        safe = {
            "_id": str(fb["_id"]),
            "user_id": str(fb.get("user_id", "")),
            "rating": fb.get("rating"),
            "category": fb.get("category"),
            "comments": fb.get("comments"),
            "product_id": str(fb["product_id"]) if fb.get("product_id") else None,
            "application_id": str(fb["application_id"]) if fb.get("application_id") else None,
        }
        print(f"  OK: rating={safe['rating']} category={safe['category']}")
    except Exception as e:
        print(f"  ERROR: {e}")

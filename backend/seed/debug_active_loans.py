"""Debug active loans 500 error."""
import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.mongodb import collections
from bson import ObjectId

print("=== Debugging active loans ===")
loans = list(collections["active_loans"].find({"user_id": {"$exists": True}}))
print(f"Total active loans: {len(loans)}")

# Find the demo user
demo = collections["users"].find_one({"email": "demo@loanwise.ai"})
if demo:
    uid = demo["_id"]
    user_loans = list(collections["active_loans"].find({"user_id": uid}))
    print(f"Demo user loans: {len(user_loans)}")
    for i, loan in enumerate(user_loans):
        print(f"\n  Loan {i+1}: {loan.get('_id')}")
        print(f"    status: {loan.get('status')}")
        print(f"    product_id type: {type(loan.get('product_id'))}")
        print(f"    application_id: {loan.get('application_id')} (type: {type(loan.get('application_id'))})")
        print(f"    recommendation_id: {loan.get('recommendation_id')}")
        print(f"    created_at type: {type(loan.get('created_at'))}")
        
        # Try to simulate _enrich_loan
        try:
            product = collections["loan_products"].find_one({"_id": loan["product_id"]})
            lender = collections["lenders"].find_one({"_id": product["lender_id"]}) if product else None
            print(f"    product_name: {product['product_name'] if product else 'NOT FOUND'}")
            print(f"    lender_name: {lender['lender_name'] if lender else 'NOT FOUND'}")
            
            # Serialize all fields manually
            from datetime import datetime, timezone
            result = {
                "_id": str(loan["_id"]),
                "user_id": str(loan["user_id"]),
                "product_id": str(loan["product_id"]),
                "recommendation_id": str(loan["recommendation_id"]) if loan.get("recommendation_id") else None,
                "application_id": str(loan["application_id"]) if loan.get("application_id") else None,
                "actual_amount": loan.get("actual_amount", 0),
                "interest_rate": loan.get("interest_rate", 0),
                "tenure_months": loan.get("tenure_months", 0),
                "emi_amount": loan.get("emi_amount", 0),
                "start_date": loan.get("start_date", ""),
                "first_due_date": loan.get("first_due_date", ""),
                "status": loan.get("status", ""),
                "product_name": product["product_name"] if product else "Unknown",
                "lender_name": lender["lender_name"] if lender else "Unknown",
                "loan_category": product["loan_category"] if product else "",
            }
            # Test JSON serialization
            import json
            serialized = json.dumps(result)
            print(f"    ✅ Serialization OK ({len(serialized)} chars)")
        except Exception as e:
            print(f"    ❌ Error: {e}")
            traceback.print_exc()

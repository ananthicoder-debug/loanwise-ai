"""Quick database state reporter."""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from database.mongodb import collections, DATABASE_NAME

print()
print("=" * 55)
print("  LOANWISE AI — DATABASE STATE REPORT")
print(f"  Database: {DATABASE_NAME}")
print("=" * 55)

total = 0
for name, col in collections.items():
    count = col.count_documents({})
    if count > 0:
        print(f"  {name:<30} {count:>6} records")
        total += count

print(f"  {'TOTAL':<30} {total:>6} records")
print()

# Demo user
u = collections["users"].find_one({"email": "demo@loanwise.ai"})
if u:
    uid = u["_id"]
    apps = list(collections["loan_applications"].find({"user_id": uid}))
    app_ids = [a["_id"] for a in apps]
    print("  DEMO USER: Arjun Mehta (demo@loanwise.ai / Demo@2026)")
    print(f"    Profile:         CIBIL=748, Income=Rs.85,000/month, IT/Tech Salaried")
    print(f"    Applications:    {len(apps)} (Personal Loan, Home Loan, Vehicle Loan)")
    print(f"    Predictions:     {collections['predictions'].count_documents({'application_id': {'$in': app_ids}})}")
    print(f"    Recommendations: {collections['recommendations'].count_documents({'application_id': {'$in': app_ids}})}")
    active = list(collections["active_loans"].find({"user_id": uid}))
    print(f"    Active Loans:    {len(active)} (1 closed, 1 active with OVERDUE EMI)")
    loan_ids = [l["_id"] for l in active]
    pay_counts = {
        status: collections["payments"].count_documents(
            {"active_loan_id": {"$in": loan_ids}, "payment_status": status}
        )
        for status in ["PAID", "OVERDUE", "UPCOMING", "DUE"]
    }
    print(f"    Payments:        PAID={pay_counts['PAID']} | OVERDUE={pay_counts['OVERDUE']} | UPCOMING={pay_counts['UPCOMING']}")
    print(f"    Documents:       {collections['documents'].count_documents({'user_id': uid})}")
    print(f"    Notifications:   {collections['notifications'].count_documents({'user_id': uid})}")
    print(f"    Feedback:        {collections['feedback'].count_documents({'user_id': uid})}")
else:
    print("  Demo user not found. Run: python seed/seed_demo_showcase.py")

print()
admin = collections["users"].find_one({"email": "admin@loanwise.ai"})
if admin:
    print("  ADMIN: System Administrator (admin@loanwise.ai / Admin@2026)")

print()
print("  LOAN CATALOGUE:")
pipeline = [
    {"$group": {"_id": "$loan_category", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
for r in collections["loan_products"].aggregate(pipeline):
    print(f"    {r['_id']:<35} {r['count']:>3} products")

print()
print("  VERIFIED LENDERS (12):")
for l in collections["lenders"].find({}, {"lender_name": 1, "lender_type": 1, "_id": 0}):
    print(f"    {l['lender_name']:<35} ({l.get('lender_type','Bank')})")

print()

# Model performance
models = list(collections["system_metadata"].find(
    {"key": {"$regex": "^model_performance_"}}
))
if models:
    print("  ML MODEL PERFORMANCE:")
    for m in models:
        metrics = m.get("metrics", {})
        print(f"    {m['model_name']}")
        print(f"      Algorithm: {m.get('algorithm','—')}  | Version: {m.get('model_version','—')}")
        print(f"      Accuracy:  {metrics.get('accuracy',0):.4f} | F1: {metrics.get('f1_score',0):.4f} | ROC-AUC: {metrics.get('roc_auc',0):.4f}")
        print(f"      Train: {m.get('training_records','—')} records | Test: {m.get('testing_records','—')} records")
        print(f"      Trained: {m.get('training_date','—')}")

print()
print("=" * 55)
print("  ALL SYSTEMS READY")
print("=" * 55)

import sys; sys.path.insert(0, '.')
from database.mongodb import collections

# Test lender name search for SBI
regex = {"$regex": "SBI", "$options": "i"}
lenders = list(collections["lenders"].find({"lender_name": regex}))
print("SBI search in lenders:", [l["lender_name"] for l in lenders])

# Test "State Bank" search
regex2 = {"$regex": "State Bank", "$options": "i"}
lenders2 = list(collections["lenders"].find({"lender_name": regex2}))
print("State Bank search:", [l["lender_name"] for l in lenders2])

# Test what the search API actually sees
query = "SBI"
regex3 = {"$regex": query, "$options": "i"}
matched_lender_ids = [l["_id"] for l in collections["lenders"].find({"lender_name": regex3})]
print(f"Matched lender IDs for '{query}': {matched_lender_ids}")

prods = list(collections["loan_products"].find({
    "is_active": True,
    "$or": [
        {"product_name": regex3},
        {"loan_category": regex3},
        {"lender_id": {"$in": matched_lender_ids}},
    ]
}).limit(5))
print(f"Products matching '{query}': {len(prods)}")
for p in prods:
    print(f"  {p.get('product_name')} lender_id={p.get('lender_id')}")

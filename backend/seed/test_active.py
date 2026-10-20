"""Quick test for active loans and all failing endpoints."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import requests

BASE = "http://127.0.0.1:8000"

print("=== Testing Active Loans Backend Connection ===\n")

# Login
r = requests.post(f"{BASE}/api/auth/login", json={"email": "demo@loanwise.ai", "password": "Demo@2026"})
print("Login status:", r.status_code, r.json().get("role"))
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}

# Admin login
ra = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@loanwise.ai", "password": "Admin@2026"})
print("Admin login status:", ra.status_code)
ATOKEN = ra.json()["access_token"]
AH = {"Authorization": f"Bearer {ATOKEN}"}

print()
print("--- [1] GET /api/active-loans ---")
r2 = requests.get(f"{BASE}/api/active-loans", headers=H)
print("Status:", r2.status_code)
if r2.status_code == 200:
    loans = r2.json()
    print(f"OK! {len(loans)} loans returned")
    for loan in loans:
        print(f"  [{loan.get('status')}] {loan.get('product_name')} by {loan.get('lender_name')}")
        print(f"  Amount: Rs.{loan.get('actual_amount'):,} | EMI: Rs.{loan.get('emi_amount'):,.2f}/month")
else:
    print("ERROR:", r2.text[:400])

print()
print("--- [2] GET /api/active-loans/{id} ---")
if r2.status_code == 200 and r2.json():
    loan_id = r2.json()[0]["_id"]
    r3 = requests.get(f"{BASE}/api/active-loans/{loan_id}", headers=H)
    print("Status:", r3.status_code)
    if r3.status_code == 200:
        loan = r3.json()
        print(f"OK! {loan.get('product_name')} | {loan.get('status')}")
    else:
        print("ERROR:", r3.text[:300])

print()
print("--- [3] GET /api/active-loans/{id}/payments ---")
if r2.status_code == 200 and r2.json():
    active = [l for l in r2.json() if l.get("status") == "active"]
    if active:
        lid = active[0]["_id"]
        r4 = requests.get(f"{BASE}/api/active-loans/{lid}/payments", headers=H)
        print("Status:", r4.status_code)
        if r4.status_code == 200:
            sched = r4.json()
            paid = sum(1 for s in sched if s["payment_status"] == "PAID")
            overdue = sum(1 for s in sched if s["payment_status"] == "OVERDUE")
            upcoming = sum(1 for s in sched if s["payment_status"] == "UPCOMING")
            print(f"OK! {len(sched)} EMIs: PAID={paid} OVERDUE={overdue} UPCOMING={upcoming}")
        else:
            print("ERROR:", r4.text[:300])

print()
print("--- [4] GET /api/admin/active-loans ---")
ra2 = requests.get(f"{BASE}/api/admin/active-loans", headers=AH)
print("Status:", ra2.status_code)
if ra2.status_code == 200:
    loans = ra2.json()
    print(f"OK! {len(loans)} loans in admin view")
    for l in loans[:3]:
        print(f"  {l.get('applicant_name')} | {l.get('product_name')} | {l.get('status')}")
else:
    print("ERROR:", ra2.text[:400])

print()
print("--- [5] GET /api/admin/model-performance ---")
rm = requests.get(f"{BASE}/api/admin/model-performance", headers=AH)
print("Status:", rm.status_code)
if rm.status_code == 200:
    models = rm.json()
    print(f"OK! {len(models)} model records")
    for m in models:
        met = m.get("metrics", {})
        print(f"  {m.get('model_name')}")
        print(f"  Accuracy={met.get('accuracy')} F1={met.get('f1_score')} ROC-AUC={met.get('roc_auc')}")
else:
    print("ERROR:", rm.text[:400])

print()
print("--- [6] GET /api/admin/feedback ---")
rf = requests.get(f"{BASE}/api/admin/feedback", headers=AH)
print("Status:", rf.status_code)
if rf.status_code == 200:
    fb = rf.json()
    print(f"OK! {len(fb)} feedback entries")
    for f in fb[:3]:
        print(f"  {f.get('user_name')}: {'★'*f.get('rating',0)} [{f.get('category')}]")
else:
    print("ERROR:", rf.text[:400])

print()
print("=== Done ===")

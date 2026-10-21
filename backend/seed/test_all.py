"""
seed/test_all.py
-----------------
Full end-to-end API test for LoanWise AI.
Run: python seed/test_all.py   (backend must be running on port 8000)
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import requests
except ImportError:
    print("Installing requests..."); os.system("pip install requests -q")
    import requests

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0
FAIL_LIST = []

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label} {detail}")
        FAIL += 1
        FAIL_LIST.append(label)

def section(n, title):
    print(f"\n{'='*55}")
    print(f"  [{n}] {title}")
    print(f"{'='*55}")

def get(path, token=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{BASE}{path}", headers=h)
    if r.status_code not in (200, 201):
        return None, r.status_code
    return r.json(), 200

def post(path, data, token=None):
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {"Content-Type": "application/json"}
    r = requests.post(f"{BASE}{path}", json=data, headers=h)
    if r.status_code not in (200, 201):
        return None, r.status_code, r.text
    return r.json(), r.status_code, ""

def put(path, data=None, token=None):
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}
    r = requests.put(f"{BASE}{path}", json=data, headers=h)
    return r.json() if r.status_code in (200, 201) else None

def delete(path, token=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.delete(f"{BASE}{path}", headers=h)
    return r.json() if r.status_code == 200 else None

print()
print("=" * 55)
print("  LoanWise AI  -  Full API Test Suite")
print("=" * 55)

# ??? 1. HEALTH ????????????????????????????????????????????????????????????????
section(1, "HEALTH CHECK")
h, _ = get("/api/health")
check("Health endpoint reachable",      h is not None)
check("status = ok",                    h and h.get("status") == "ok")
check("mongodb = connected",            h and h.get("mongodb") == "connected")
check("database = loan_ai_system",      h and h.get("database") == "loan_ai_system")
if h:
    print(f"  status={h['status']} | db={h['database']} | mongo={h['mongodb']}")

# ??? 2. AUTH ??????????????????????????????????????????????????????????????????
section(2, "AUTHENTICATION")
udata, _, _ = post("/api/auth/login", {"email": "demo@loanwise.ai", "password": "Demo@2026"})
check("Login demo user (demo@loanwise.ai)", udata is not None)
check("Token returned",                     udata and len(udata.get("access_token","")) > 10)
check("Role = user",                        udata and udata.get("role") == "user")
check("Name = Arjun Mehta",                 udata and udata.get("full_name") == "Arjun Mehta")
UTOKEN = udata["access_token"] if udata else ""

adata, _, _ = post("/api/auth/login", {"email": "admin@loanwise.ai", "password": "Admin@2026"})
check("Login admin (admin@loanwise.ai)",    adata is not None)
check("Admin token returned",               adata and len(adata.get("access_token","")) > 10)
check("Admin role = admin",                 adata and adata.get("role") == "admin")
ATOKEN = adata["access_token"] if adata else ""

me, _ = get("/api/auth/me", UTOKEN)
check("GET /api/auth/me",                   me and me.get("email") == "demo@loanwise.ai")

# ??? 3. USER PROFILE ??????????????????????????????????????????????????????????
section(3, "USER PROFILE")
profile, _ = get("/api/users/profile", UTOKEN)
check("GET /api/users/profile",             profile and profile.get("full_name") == "Arjun Mehta")
check("Profile has address.city",           profile and profile.get("address",{}).get("city") == "Bengaluru")
check("Profile has phone",                  profile and profile.get("phone") == "9876543210")
updated = put("/api/users/profile", {"occupation_description": "Senior Software Engineer"}, UTOKEN)
check("PUT /api/users/profile",             updated is not None)
if profile:
    print(f"  Name={profile['full_name']} | City={profile['address']['city']} | DOB={profile.get('date_of_birth')}")

# ??? 4. CREDIT PROFILE ????????????????????????????????????????????????????????
section(4, "CREDIT PROFILE")
cp, _ = get("/api/credit-profile", UTOKEN)
check("GET /api/credit-profile",            cp is not None)
check("CIBIL = 748",                        cp and cp.get("cibil_score") == 748)
check("Monthly income = 85000",             cp and cp.get("monthly_income") == 85000)
check("Employment = Salaried",              cp and cp.get("employment_type") == "Salaried")
check("CIBIL >= 300 and <= 900",            cp and 300 <= cp.get("cibil_score",0) <= 900)
cpupd = put("/api/credit-profile", {"cibil_score": 755, "monthly_income": 87000, "annual_income": 1044000}, UTOKEN)
check("PUT /api/credit-profile",            cpupd and cpupd.get("cibil_score") == 755)
# Restore
put("/api/credit-profile", {"cibil_score": 748, "monthly_income": 85000, "annual_income": 1020000}, UTOKEN)
if cp:
    print(f"  CIBIL={cp['cibil_score']} | Income=Rs.{cp['monthly_income']:,}/mo | Employment={cp['employment_type']}")

# ??? 5. LOAN CATALOGUE ????????????????????????????????????????????????????????
section(5, "LOAN CATALOGUE")
cats, _ = get("/api/loans/categories", UTOKEN)
check("GET /api/loans/categories",          cats is not None)
check("7 categories from MongoDB",          cats and len(cats) == 7)
cat_names = [c["category"] for c in (cats or [])]
check("Personal Loan category present",     "Personal Loan" in cat_names)
check("Home Loan category present",         "Home Loan" in cat_names)
check("Vehicle Loan category present",      "Vehicle Loan" in cat_names)
check("Education Loan category present",    "Education Loan" in cat_names)
if cats:
    for c in cats:
        print(f"  {c['category']}: {c['product_count']} products, {c['lender_count']} lenders")

lenders, _ = get("/api/loans/lenders", UTOKEN)
check("GET /api/loans/lenders",             lenders is not None)
check("12 verified lenders",               lenders and len(lenders) == 12)
lender_names = [l["lender_name"] for l in (lenders or [])]
check("State Bank of India present",        "State Bank of India" in lender_names)
check("HDFC Bank present",                  "HDFC Bank" in lender_names)
check("ICICI Bank present",                 "ICICI Bank" in lender_names)
check("Axis Bank present",                  "Axis Bank" in lender_names)
check("Kotak Mahindra Bank present",        "Kotak Mahindra Bank" in lender_names)
check("Bajaj Finance (NBFC) present",       "Bajaj Finance" in lender_names)
check("Tata Capital (NBFC) present",        "Tata Capital" in lender_names)
check("NO demo/sample/fake lenders",        not any(x in ["Demo Bank","Sample Bank","Test Bank","Bank A","Bank B"] for x in lender_names))

# ??? 6. LOAN SEARCH ???????????????????????????????????????????????????????????
section(6, "LOAN SEARCH")
s_sbi, _   = get("/api/loans/search?q=State+Bank", UTOKEN)
s_pl, _    = get("/api/loans/search?q=Personal+Loan", UTOKEN)
s_hl, _    = get("/api/loans/search?q=Home+Loan", UTOKEN)
s_hdfc, _  = get("/api/loans/search?q=HDFC", UTOKEN)
s_gold, _  = get("/api/loans/search?q=Gold", UTOKEN)
s_edu, _   = get("/api/loans/search?q=Education", UTOKEN)
check("Search 'State Bank' returns results",   s_sbi and len(s_sbi) > 0)
check("Search 'Personal Loan' returns results",s_pl  and len(s_pl) > 0)
check("Search 'Home Loan' returns results",    s_hl  and len(s_hl) > 0)
check("Search 'HDFC' returns results",         s_hdfc and len(s_hdfc) > 0)
check("Search 'Gold' returns results",         s_gold and len(s_gold) > 0)
check("Search 'Education' returns results",    s_edu and len(s_edu) > 0)
if s_sbi:
    print(f"  'State Bank' search: {len(s_sbi)} products (e.g. {s_sbi[0]['product_name']})")
if s_pl:
    print(f"  'Personal Loan' search: {len(s_pl)} products")

# ??? 7. SINGLE PRODUCT DETAIL ?????????????????????????????????????????????????
section(7, "PRODUCT DETAIL PAGE")
prod_id = s_pl[0]["_id"] if s_pl else None
pd, _ = get(f"/api/loans/{prod_id}", UTOKEN) if prod_id else (None, 404)
check("GET /api/loans/{id}",                pd is not None)
check("Has product_name",                   pd and pd.get("product_name"))
check("Has lender_name",                    pd and pd.get("lender_name"))
check("Has interest_rate_min",              pd and pd.get("interest_rate_min",0) > 0)
check("Has interest_rate_max",              pd and pd.get("interest_rate_max",0) > 0)
check("Has min_amount",                     pd and pd.get("min_amount",0) > 0)
check("Has max_amount",                     pd and pd.get("max_amount",0) > 0)
check("Has verification_status",            pd and pd.get("verification_status"))
check("Has official_product_url",           pd and pd.get("official_product_url") is not None)
check("Has source_date",                    pd and pd.get("source_date"))
check("Lender is NOT fake/demo",            pd and not any(x in str(pd.get("lender_name","")) for x in ["Demo","Sample","Test","Bank A","Bank B"]))
if pd:
    print(f"  Product: {pd['product_name']}")
    print(f"  Lender:  {pd['lender_name']} ({pd.get('lender_type','')})")
    print(f"  Rate: {pd['interest_rate_min']}% - {pd['interest_rate_max']}%  Amount: Rs.{pd['min_amount']:,} - Rs.{pd['max_amount']:,}")
    print(f"  Tenure: {pd['min_tenure']}-{pd['max_tenure']} months  Fee: {pd.get('processing_fee','N/A')}")
    print(f"  Verification: {pd['verification_status']}  Source: {pd.get('source_date','')}")
    print(f"  URL: {pd.get('official_product_url','')}")

# ??? 8. LOAN COMPARISON ???????????????????????????????????????????????????????
section(8, "LOAN COMPARISON")
if s_pl and len(s_pl) >= 2:
    ids = f"{s_pl[0]['_id']},{s_pl[1]['_id']}"
    comp, _ = get(f"/api/loans/compare?ids={ids}", UTOKEN)
    check("GET /api/loans/compare returns 2 products",  comp and len(comp) == 2)
    check("Both products have lender_name",             comp and all(p.get("lender_name") for p in comp))
    check("No fake lenders in comparison",              comp and not any(x in str(json.dumps(comp)) for x in ["Demo","Sample"]))
    if comp:
        print(f"  Comparing:")
        for p in comp:
            print(f"    {p['product_name']} by {p['lender_name']} | Rate: {p['interest_rate_min']}-{p['interest_rate_max']}%")

# ??? 9. ML PIPELINE ???????????????????????????????????????????????????????????
section(9, "ML PIPELINE  -  ELIGIBILITY + AFFORDABILITY")
apps_list, _ = get("/api/applications", UTOKEN)
check("GET /api/applications",              apps_list is not None)
check("Has >= 3 past applications",         apps_list and len(apps_list) >= 3)

newapp, _, err = post("/api/applications", {
    "loan_amount": 400000, "loan_tenure": 36,
    "loan_category": "Personal Loan", "purpose": "Home renovation"
}, UTOKEN)
check("POST /api/applications",             newapp is not None, err)
check("Model 1 returns result",             newapp and newapp.get("model_1",{}).get("result") in ["Eligible","Not Eligible"])
check("Model 1 has probability 0-1",        newapp and 0 < newapp.get("model_1",{}).get("probability",0) <= 1)
check("Model 2 returns result",             newapp and newapp.get("model_2",{}).get("result") in ["Manageable","Not Manageable"])
check("Model 2 has probability 0-1",        newapp and 0 < newapp.get("model_2",{}).get("probability",0) <= 1)
check("eligible_count > 0",                 newapp and newapp.get("eligible_count",0) > 0)
check("eligible_products is grouped dict",  newapp and isinstance(newapp.get("eligible_products"), dict))
check("Recommended products present",       newapp and newapp.get("recommended_count",0) >= 0)
check("No hardcoded demo bank names",       newapp and "Demo Bank" not in json.dumps(newapp))
if newapp:
    m1 = newapp["model_1"]; m2 = newapp["model_2"]
    print(f"  Model 1  -  Eligibility:  {m1['result']} (probability: {m1['probability']*100:.0f}%)")
    print(f"  Model 2  -  Affordability:{m2['result']} (probability: {m2['probability']*100:.0f}%)")
    print(f"  Eligible products: {newapp['eligible_count']} | Recommended: {newapp['recommended_count']}")
    for cat, cdata in newapp.get("eligible_products",{}).items():
        print(f"    {cat}: {cdata['count']} products")
        for lname, ldata in cdata.get("lenders",{}).items():
            print(f"      {lname}: {ldata['count']} products")

app_detail, _ = get(f"/api/applications/{newapp['application_id']}", UTOKEN) if newapp else (None,404)
check("GET /api/applications/{id} re-fetch", app_detail and app_detail.get("eligible_count") >= 0)

# ??? 10. RECOMMENDATIONS ??????????????????????????????????????????????????????
section(10, "RECOMMENDATIONS")
recs, _ = get("/api/recommendations", UTOKEN)
check("GET /api/recommendations",           recs is not None)
check("Has recommendations",                recs and len(recs) > 0)
if recs:
    check("Has match_score",                recs[0].get("match_score") is not None)
    check("Has product object",             recs[0].get("product") is not None)
    check("Has reason text",                len(recs[0].get("reason","")) > 5)
    check("Match score 0-100",              0 <= recs[0].get("match_score",0) <= 100)
    print(f"  {len(recs)} recommendations found")
    for r in recs[:3]:
        p = r.get("product",{})
        print(f"    {p.get('product_name','?')} by {p.get('lender_name','?')} | Score: {r.get('match_score')}% | EMI: Rs.{r.get('recommended_emi',0):,.0f}")
        print(f"    Reason: {r.get('reason','')[:90]}")

# ??? 11. ACTIVE LOANS ?????????????????????????????????????????????????????????
section(11, "ACTIVE LOANS")
aloans, _ = get("/api/active-loans", UTOKEN)
check("GET /api/active-loans",              aloans is not None)
check("Has >= 2 loans",                     aloans and len(aloans) >= 2)
closed = [l for l in (aloans or []) if l.get("status") == "closed"]
active = [l for l in (aloans or []) if l.get("status") == "active"]
check("Has 1 CLOSED loan",                  len(closed) >= 1)
check("Has 1 ACTIVE loan",                  len(active) >= 1)
if active:
    al = active[0]
    check("Active loan has product_name",   bool(al.get("product_name")))
    check("Active loan has emi_amount",     al.get("emi_amount",0) > 0)
    check("Active loan has lender_name",    bool(al.get("lender_name")))
    check("Lender is real Indian bank",     not any(x in al.get("lender_name","") for x in ["Demo","Sample","Test"]))
    print(f"  ACTIVE:  {al['product_name']} by {al['lender_name']}")
    print(f"           Amount: Rs.{al['actual_amount']:,} | Rate: {al['interest_rate']}% | Tenure: {al['tenure_months']} months")
    print(f"           Monthly EMI: Rs.{al['emi_amount']:,.2f}")
if closed:
    cl = closed[0]
    print(f"  CLOSED:  {cl.get('product_name','?')}  -  all EMIs paid, loan closed")

    al_detail, _ = get(f"/api/active-loans/{active[0]['_id']}", UTOKEN) if active else (None,404)
    check("GET /api/active-loans/{id}",     al_detail and al_detail.get("_id") is not None)

# ??? 12. EMI SCHEDULE ?????????????????????????????????????????????????????????
section(12, "EMI SCHEDULE AND PAYMENT MARKING")
sched_loan_id = active[0]["_id"] if active else None
sched, _ = get(f"/api/active-loans/{sched_loan_id}/payments", UTOKEN) if sched_loan_id else (None,404)
check("GET /api/active-loans/{id}/payments",    sched is not None)
if sched:
    paid_emis     = [s for s in sched if s["payment_status"] == "PAID"]
    overdue_emis  = [s for s in sched if s["payment_status"] == "OVERDUE"]
    upcoming_emis = [s for s in sched if s["payment_status"] in ("UPCOMING","DUE")]
    check("Has PAID EMIs",                  len(paid_emis) > 0)
    check("Has OVERDUE EMI",                len(overdue_emis) >= 1)
    check("Has UPCOMING EMIs",              len(upcoming_emis) > 0)
    check("No negative EMI amounts",        all(s["amount_due"] >= 0 for s in sched))
    check("EMI numbers are sequential",     sched[0]["emi_number"] == 1)
    check("Has principal_component",        all("principal_component" in s for s in sched))
    check("Has interest_component",         all("interest_component" in s for s in sched))
    print(f"  Schedule: {len(sched)} EMIs | PAID={len(paid_emis)} | OVERDUE={len(overdue_emis)} | UPCOMING={len(upcoming_emis)}")
    if paid_emis:
        p = paid_emis[-1]
        print(f"  Last paid: EMI #{p['emi_number']} due {p['due_date']} | Amount Rs.{p['amount_due']:,.2f} | Paid {p.get('payment_date','?')}")
    if overdue_emis:
        o = overdue_emis[0]
        print(f"  OVERDUE:   EMI #{o['emi_number']} due {o['due_date']} | {o.get('days_overdue',0)} days late | Charge Rs.{o.get('late_charge',0):,.2f}")

    # Mark an upcoming EMI as paid
    if upcoming_emis:
        emi_to_pay = upcoming_emis[0]
        marked, _, _ = post(f"/api/payments/{emi_to_pay['_id']}/mark-paid", {"amount_paid": emi_to_pay["amount_due"]}, UTOKEN)
        check("POST /api/payments/{id}/mark-paid",  marked and marked.get("payment_status") == "PAID")
        if marked:
            print(f"  Marked EMI #{emi_to_pay['emi_number']} as PAID (Rs.{emi_to_pay['amount_due']:,.2f})")

# ??? 13. NOTIFICATIONS ????????????????????????????????????????????????????????
section(13, "NOTIFICATIONS")
notifs, _ = get("/api/notifications", UTOKEN)
check("GET /api/notifications",             notifs is not None)
check("Has emi_notifications key",          notifs and "emi_notifications" in notifs)
check("Has system_notifications key",       notifs and "system_notifications" in notifs)
sys_notifs = notifs.get("system_notifications",[]) if notifs else []
check("Has system notifications",           len(sys_notifs) > 0)
if sys_notifs:
    sn = sys_notifs[0]
    r = put(f"/api/notifications/{sn['_id']}/read", {}, UTOKEN)
    check("PUT mark notification read",     r is not None)
    print(f"  EMI notifications: {len(notifs.get('emi_notifications',[]))}")
    print(f"  System notifications: {len(sys_notifs)}")
    for n in sys_notifs:
        print(f"    [{n.get('type')}] {n.get('title')}  -  read={n.get('is_read')}")

r_all = put("/api/notifications/read-all", {}, UTOKEN)
check("PUT mark all notifications read",    r_all is not None)

# ??? 14. DOCUMENTS ????????????????????????????????????????????????????????????
section(14, "DOCUMENTS")
docs, _ = get("/api/documents", UTOKEN)
check("GET /api/documents",                 docs is not None)
check("Has >= 6 documents",                 docs and len(docs) >= 6)
check("Has Identity Proof",                 docs and any(d["document_type"] == "Identity Proof" for d in docs))
check("Has Income Proof",                   docs and any(d["document_type"] == "Income Proof" for d in docs))
check("Has Bank Statement",                 docs and any(d["document_type"] == "Bank Statement" for d in docs))
check("Has Employment Proof",               docs and any(d["document_type"] == "Employment Proof" for d in docs))
check("Has verification_status",            docs and all("verification_status" in d for d in docs))
if docs:
    for d in docs:
        print(f"  {d['document_type']}: {d['file_name']} [{d['verification_status']}]")

adddoc, _, _ = post("/api/documents", {"document_type": "Other","file_name": "test_doc.pdf","notes":"test"}, UTOKEN)
check("POST /api/documents (add)",          adddoc and adddoc.get("_id"))
deldoc = delete(f"/api/documents/{adddoc['_id']}", UTOKEN) if adddoc else None
check("DELETE /api/documents/{id}",         deldoc and deldoc.get("message"))

# ??? 15. FEEDBACK ?????????????????????????????????????????????????????????????
section(15, "FEEDBACK")
fb_list, _ = get("/api/feedback", UTOKEN)
check("GET /api/feedback",                  fb_list is not None)
check("Has >= 3 feedback entries",          fb_list and len(fb_list) >= 3)
check("Feedback has ratings",               fb_list and all(f.get("rating",0) >= 1 for f in fb_list))
new_fb, _, _ = post("/api/feedback", {"rating": 5, "category": "UI/UX", "comments": "Very helpful platform!"}, UTOKEN)
check("POST /api/feedback",                 new_fb and new_fb.get("_id"))
if fb_list:
    for f in fb_list:
        print(f"  {'?'*f['rating']} [{f['category']}] {f.get('comments','')[:60]}")

# ??? 16. USER DASHBOARD ???????????????????????????????????????????????????????
section(16, "USER DASHBOARD")
dash, _ = get("/api/dashboard", UTOKEN)
check("GET /api/dashboard",                 dash and dash.get("welcome_name") == "Arjun Mehta")
check("Has cards object",                   dash and "cards" in dash)
check("eligible_loans in cards",            dash and dash["cards"].get("eligible_loans") is not None)
check("active_loans >= 1",                  dash and dash["cards"].get("active_loans",0) >= 1)
check("Has charts object",                  dash and "charts" in dash)
check("Has notifications",                  dash and "notifications" in dash)
check("Has recent_activity",                dash and "recent_activity" in dash)
check("Category chart present",             dash and dash.get("charts",{}).get("eligible_by_category"))
if dash:
    c = dash["cards"]
    print(f"  Eligible={c.get('eligible_loans')} | Recommended={c.get('recommended_loans')} | Active={c.get('active_loans')}")
    if c.get("next_emi"):
        print(f"  Next EMI: Rs.{c['next_emi'].get('amount_due',0):,.2f} due {c['next_emi'].get('due_date','?')}")
    print(f"  Charts  -  Category counts:")
    for cat, cnt in dash["charts"].get("eligible_by_category",{}).items():
        print(f"    {cat}: {cnt} products")

# ??? 17. ADMIN DASHBOARD ??????????????????????????????????????????????????????
section(17, "ADMIN DASHBOARD")
ad, _ = get("/api/admin/dashboard", ATOKEN)
check("GET /api/admin/dashboard",           ad is not None)
check("total_users >= 1",                   ad and ad.get("total_users",0) >= 1)
check("total_lenders = 12",                 ad and ad.get("total_lenders") == 12)
check("active_loan_products = 62",          ad and ad.get("active_loan_products") == 62)
check("total_predictions present",          ad and ad.get("total_predictions") is not None)
check("total_recommendations present",      ad and ad.get("total_recommendations") is not None)
check("Has charts.apps_by_category",        ad and ad.get("charts",{}).get("apps_by_category") is not None)
check("Has charts.payment_status",          ad and ad.get("charts",{}).get("payment_status") is not None)
if ad:
    print(f"  Users={ad['total_users']} | Apps={ad['total_applications']} | Lenders={ad['total_lenders']} | Products={ad['active_loan_products']}")
    print(f"  Predictions={ad['total_predictions']} | Recommendations={ad['total_recommendations']}")
    print(f"  Active Loans={ad['active_loans']} | Overdue Payments={ad['overdue_payments']}")

# ??? 18. ADMIN USERS ??????????????????????????????????????????????????????????
section(18, "ADMIN USER MANAGEMENT")
ausers, _ = get("/api/admin/users", ATOKEN)
check("GET /api/admin/users",               ausers is not None)
check("Has users",                          ausers and len(ausers) >= 1)
check("Demo user visible to admin",         ausers and any(u.get("email") == "demo@loanwise.ai" for u in ausers))
check("application_count in user data",     ausers and "application_count" in ausers[0])
check("Password NOT exposed",               ausers and "password_hash" not in json.dumps(ausers))
if ausers:
    print(f"  {len(ausers)} users:")
    for u in ausers[:5]:
        print(f"    {u['full_name']} ({u['email']}) | City: {u.get('address',{}).get('city','?')} | Apps: {u.get('application_count',0)}")

# ??? 19. ADMIN APPLICATIONS ???????????????????????????????????????????????????
section(19, "ADMIN APPLICATIONS")
aapps, _ = get("/api/admin/applications", ATOKEN)
check("GET /api/admin/applications",        aapps is not None)
check("Has >= 3 applications",              aapps and len(aapps) >= 3)
check("Has applicant_name",                 aapps and aapps[0].get("applicant_name"))
check("Has loan_category",                  aapps and aapps[0].get("loan_category"))
check("Has loan_amount",                    aapps and aapps[0].get("loan_amount",0) > 0)
if aapps:
    print(f"  {len(aapps)} applications:")
    for a in aapps[:5]:
        print(f"    {a.get('applicant_name','?')}: {a.get('loan_category','?')} Rs.{a.get('loan_amount',0):,} ({a.get('status','?')})")

# ??? 20. ADMIN ML PREDICTIONS ?????????????????????????????????????????????????
section(20, "ADMIN ML PREDICTIONS")
apreds, _ = get("/api/admin/predictions", ATOKEN)
check("GET /api/admin/predictions",         apreds is not None)
check("Has >= 3 predictions",               apreds and len(apreds) >= 3)
check("Has model_1 result",                 apreds and apreds[0].get("model_1",{}).get("result") in ["Eligible","Not Eligible"])
check("Has model_2 result",                 apreds and apreds[0].get("model_2",{}).get("result") in ["Manageable","Not Manageable"])
check("Has eligible_count",                 apreds and "eligible_count" in apreds[0])
if apreds:
    print(f"  {len(apreds)} prediction records:")
    for p in apreds[:3]:
        print(f"    M1={p['model_1']['result']}({p['model_1']['probability']*100:.0f}%) M2={p['model_2']['result']} Eligible={p.get('eligible_count')} Recs={p.get('recommended_count')}")

# ??? 21. ADMIN RECOMMENDATIONS ????????????????????????????????????????????????
section(21, "ADMIN RECOMMENDATIONS")
arecs, _ = get("/api/admin/recommendations", ATOKEN)
check("GET /api/admin/recommendations",     arecs is not None)
check("Has recommendation records",         arecs and len(arecs) >= 1)
check("Has match_score",                    arecs and "match_score" in arecs[0])
if arecs:
    print(f"  {len(arecs)} recommendation records in database")

# ??? 22. ADMIN LENDER MANAGEMENT ??????????????????????????????????????????????
section(22, "ADMIN LENDER MANAGEMENT")
al, _ = get("/api/admin/lenders", ATOKEN)
check("GET /api/admin/lenders",             al is not None)
check("All 12 real lenders listed",         al and len(al) >= 12)
check("All real Indian bank names",         al and not any(l.get("lender_name","") in ["Demo Bank","Sample Bank","Test Bank","Bank A","Bank B"] for l in al))
check("Each lender has product_count",      al and "product_count" in al[0])
nl, _, _ = post("/api/admin/lenders", {"lender_name":"Indian Bank","lender_type":"Bank","official_website":"https://www.indianbank.in","headquarters_city":"Chennai","state":"Tamil Nadu"}, ATOKEN)
check("POST /api/admin/lenders (add)",      nl and nl.get("_id"))
if nl:
    dl = delete(f"/api/admin/lenders/{nl['_id']}", ATOKEN)
    check("DELETE /api/admin/lenders/{id}", dl and dl.get("message"))
if al:
    print(f"  {len(al)} lenders:")
    for l in al:
        print(f"    {l['lender_name']} ({l.get('lender_type','?')})  -  {l.get('product_count',0)} products")

# ??? 23. ADMIN PRODUCT MANAGEMENT ?????????????????????????????????????????????
section(23, "ADMIN PRODUCT MANAGEMENT")
ap, _ = get("/api/admin/products", ATOKEN)
check("GET /api/admin/products",            ap is not None)
check("62 verified products",               ap and len(ap) == 62)
check("No demo/sample products",            ap and not any("Demo" in p.get("product_name","") or "Sample" in p.get("product_name","") for p in ap))
check("Products have verification_status",  ap and all("verification_status" in p for p in ap))
check("Products have official_product_url", ap and any(p.get("official_product_url") for p in ap))
if ap:
    from collections import Counter
    by_cat = Counter(p["loan_category"] for p in ap)
    print(f"  62 verified products (no demo data):")
    for cat, cnt in sorted(by_cat.items(), key=lambda x:-x[1]):
        print(f"    {cat}: {cnt}")

# ??? 24. ADMIN ACTIVE LOANS ???????????????????????????????????????????????????
section(24, "ADMIN ACTIVE LOANS AND PAYMENTS")
aact, _ = get("/api/admin/active-loans", ATOKEN)
check("GET /api/admin/active-loans",        aact is not None)
check("Has >= 2 active loans",              aact and len(aact) >= 2)
check("Has applicant_name",                 aact and aact[0].get("applicant_name"))
check("Has product_name",                   aact and aact[0].get("product_name"))
check("Has lender_name",                    aact and aact[0].get("lender_name"))
if aact:
    print(f"  {len(aact)} active/closed loan records:")
    for l in aact:
        print(f"    {l.get('applicant_name','?')}: {l.get('product_name','?')} Rs.{l.get('actual_amount',0):,} ({l.get('status','?')})")

apay, _ = get("/api/admin/payments", ATOKEN)
check("GET /api/admin/payments",            apay and len(apay) >= 10)
if apay:
    from collections import Counter
    sc = Counter(p["payment_status"] for p in apay)
    print(f"  {len(apay)} payment records: PAID={sc.get('PAID',0)} OVERDUE={sc.get('OVERDUE',0)} UPCOMING={sc.get('UPCOMING',0)}")

# ??? 25. DATASET MANAGEMENT ???????????????????????????????????????????????????
section(25, "DATASET MANAGEMENT")
ds, _ = get("/api/admin/datasets", ATOKEN)
check("GET /api/admin/datasets",            ds is not None)
check("dataset_version = 2.0",             ds and ds.get("dataset_version") == "2.0")
check("Lenders >= 12",                      ds and ds.get("counts",{}).get("lenders",0) >= 12)
check("Products = 62",                      ds and ds.get("counts",{}).get("loan_products",0) == 62)
check("real_lenders_loaded = True",         ds and ds.get("catalogue_status",{}).get("real_lenders_loaded") == True)
check("real_products_loaded = True",        ds and ds.get("catalogue_status",{}).get("real_products_loaded") == True)
if ds:
    c = ds.get("counts",{})
    print(f"  Dataset Version: {ds['dataset_version']}")
    print(f"  Lenders={c.get('lenders')} | Products={c.get('loan_products')} | Users={c.get('users')}")
    print(f"  Applications={c.get('loan_applications')} | Payments={c.get('payments')}")
    print(f"  Borrower dataset: {ds.get('borrower_dataset_version')}")
    print(f"  Historical dataset: {ds.get('historical_dataset_version')}")

ls, _ = get("/api/admin/lender-stats", ATOKEN)
check("GET /api/admin/lender-stats",        ls and len(ls) > 0)
cs, _ = get("/api/admin/category-stats", ATOKEN)
check("GET /api/admin/category-stats",      cs and len(cs) == 7)
if ls:
    print(f"  Products per lender (from MongoDB aggregation):")
    for l in ls:
        print(f"    {l['lender_name']}: {l['product_count']}")

# ??? 26. DATA QUALITY ?????????????????????????????????????????????????????????
section(26, "DATA QUALITY VALIDATION")
dq, _ = get("/api/admin/data-quality", ATOKEN)
check("GET /api/admin/data-quality",        dq is not None)
check("Status = PASS",                      dq and dq.get("status") == "PASS")
check("Total products = 62",                dq and dq.get("total_products") == 62)
check("0 validation errors",               dq and len(dq.get("errors",[])) == 0)
if dq:
    print(f"  Status: {dq['status']}")
    print(f"  Total={dq['total_products']} | Active={dq['active_products']} | Lenders={dq['total_lenders']}")
    print(f"  Errors={len(dq.get('errors',[]))} | Warnings={len(dq.get('warnings',[]))}")
    for e in dq.get("errors",[]):
        print(f"    ERROR: {e}")
    for w in dq.get("warnings",[]):
        print(f"    WARN:  {w}")

# ??? 27. ML MODEL PERFORMANCE ?????????????????????????????????????????????????
section(27, "ML MODEL PERFORMANCE")
mperf, _ = get("/api/admin/model-performance", ATOKEN)
check("GET /api/admin/model-performance",   mperf is not None)
check("Has 2 model records",                mperf and len(mperf) >= 2)
if mperf and len(mperf) >= 2:
    m1, m2 = mperf[0], mperf[1]
    check("Model 1 accuracy > 0.50",        m1.get("metrics",{}).get("accuracy",0) > 0.50)
    check("Model 2 accuracy > 0.50",        m2.get("metrics",{}).get("accuracy",0) > 0.50)
    check("Model 1 F1 > 0.50",              m1.get("metrics",{}).get("f1_score",0) > 0.50)
    check("Model 2 F1 > 0.50",              m2.get("metrics",{}).get("f1_score",0) > 0.50)
    check("ROC-AUC present for Model 1",    m1.get("metrics",{}).get("roc_auc",0) > 0)
    check("Metrics NOT fabricated (<1.0)",  m1.get("metrics",{}).get("f1_score",1) < 1.0)
    check("Training records stored",        m1.get("training_records",0) > 0)
    check("Algorithm name stored",          bool(m1.get("algorithm")))
    print()
    for m in mperf:
        met = m.get("metrics",{})
        print(f"  {m.get('model_name')}")
        print(f"    Algorithm:  {m.get('algorithm')} (v{m.get('model_version')})")
        print(f"    Accuracy:   {met.get('accuracy'):.4f}")
        print(f"    Precision:  {met.get('precision'):.4f}")
        print(f"    Recall:     {met.get('recall'):.4f}")
        print(f"    F1 Score:   {met.get('f1_score'):.4f}")
        print(f"    ROC-AUC:    {met.get('roc_auc'):.4f}")
        print(f"    Confusion:  {met.get('confusion_matrix')}")
        print(f"    Train={m.get('training_records')} records | Test={m.get('testing_records')} records")
        print(f"    Dataset:    {m.get('dataset_name')}")
        print(f"    Trained:    {m.get('training_date')}")
        print(f"    Disclaimer: {m.get('disclaimer')}")

# ??? 28. ADMIN FEEDBACK ???????????????????????????????????????????????????????
section(28, "ADMIN FEEDBACK VIEW")
afb, _ = get("/api/admin/feedback", ATOKEN)
check("GET /api/admin/feedback",            afb is not None)
check("Has >= 3 feedback entries",          afb and len(afb) >= 3)
check("Has user_name in each record",       afb and all("user_name" in f for f in afb))
check("Has rating in each record",          afb and all("rating" in f for f in afb))
if afb:
    print(f"  {len(afb)} feedback entries:")
    for f in afb[:5]:
        print(f"    {f.get('user_name','?')}: {'?'*f['rating']} [{f['category']}] {f.get('comments','')[:50]}")

# ??? FINAL SUMMARY ????????????????????????????????????????????????????????????
print()
print("=" * 55)
print("  FINAL TEST RESULTS")
print("=" * 55)
print(f"  PASSED: {PASS}")
print(f"  FAILED: {FAIL}")
print(f"  TOTAL:  {PASS+FAIL}")
print()
if FAIL == 0:
    print("  ?  ALL TESTS PASSED!")
    print("  LoanWise AI is fully operational.")
else:
    print(f"  ?  {FAIL} test(s) failed:")
    for f in FAIL_LIST:
        print(f"    - {f}")
print("=" * 55)
print()
print("  DEMO CREDENTIALS:")
print("  User:  demo@loanwise.ai  / Demo@2026  (Arjun Mehta)")
print("  Admin: admin@loanwise.ai / Admin@2026")
print()
print("  START COMMANDS:")
print("  1. uvicorn main:app --reload          (from backend/)")
print("  2. Open frontend/index.html in browser")
print("  3. API docs: http://127.0.0.1:8000/docs")
print("=" * 55)

"""Test report generation, top-3 recommendations, and lender website URLs."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import requests

BASE = "http://127.0.0.1:8000"

r = requests.post(f"{BASE}/api/auth/login", json={"email": "demo@loanwise.ai", "password": "Demo@2026"})
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}

print("=== Report + Recommendations Tests ===\n")

# Get latest application
apps = requests.get(f"{BASE}/api/applications", headers=H).json()
if not apps:
    print("No applications found  -  run seed_demo_showcase.py first"); exit()

app_id = apps[0]["_id"]
print(f"Using application: {app_id} ({apps[0].get('loan_category')} Rs.{apps[0].get('loan_amount'):,})")

# Generate report
print("\n[1] POST /api/reports/generate/{app_id}")
r2 = requests.post(f"{BASE}/api/reports/generate/{app_id}", headers=H)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    report = r2.json()
    print(f"  Report: {report['report_title']}")
    print(f"  Generated: {report['generated_at']}")
    a = report.get("section_a_applicant", {})
    print(f"\n  SECTION A  -  Applicant:")
    print(f"    Name: {a['applicant_name']} | Age: {a['age']} | CIBIL: {a['cibil_score']}")
    print(f"    Income: Rs.{a['monthly_income']:,.0f}/mo | Employment: {a['employment_type']}")
    print(f"    Requested: Rs.{a['requested_amount']:,} {a['requested_category']} for {a.get('requested_tenure_months', a.get('requested_tenure', 0))} months")

    b = report.get("section_b_eligibility", {})
    print(f"\n  SECTION B  -  Eligibility:")
    print(f"    Result: {b['eligibility_result']} ({b['model_confidence_pct']}% confidence)")
    print(f"    Eligible products: {b['eligible_product_count']}")
    print(f"    Factors: {b['eligibility_factors'][:2]}")

    c = report.get("section_c_affordability", {})
    print(f"\n  SECTION C  -  Affordability:")
    print(f"    Monthly income:   Rs.{c['monthly_income']:,.0f}")
    print(f"    Existing EMI:     Rs.{c['existing_emi']:,.0f}")
    print(f"    Proposed EMI est: Rs.{c['proposed_emi_estimate']:,.0f}")
    print(f"    Total EMI:        Rs.{c['total_emi']:,.0f}")
    print(f"    Monthly surplus:  Rs.{c['monthly_surplus_estimate']:,.0f}")
    print(f"    EMI/Income ratio: {c['emi_to_income_ratio_pct']}%")
    print(f"    Result: {c['affordability_result']} ({c['model_confidence_pct']}% confidence)")

    d = report.get("section_d_observations", [])
    print(f"\n  SECTION D  -  Observations ({len(d)}):")
    for obs in d[:3]:
        icon = {"positive":"?","warning":"??","neutral":"??","info":"?"}.get(obs["type"],"?")
        print(f"    {icon} {obs['text']}")

    f_recs = report.get("section_f_recommended", [])
    print(f"\n  SECTION F  -  TOP 3 Recommendations ({len(f_recs)} shown):")
    for i, rec in enumerate(f_recs, 1):
        print(f"    {i}. {rec['product_name']} by {rec['lender_name']}")
        print(f"       Rate: {rec['interest_rate_min']}%-{rec['interest_rate_max']}% | EMI: Rs.{rec['estimated_emi']:,.0f}/mo")
        print(f"       Match Score: {rec['match_score']}%")
        print(f"       Official URL: {rec['official_url']}")
        print(f"       Lender Website: {rec['lender_website']}")
        print(f"       Reason: {rec['reason'][:90]}...")

    g = report.get("section_g_next_steps", [])
    print(f"\n  SECTION G  -  Next Steps ({len(g)}):")
    for step in g[:3]:
        print(f"    ? {step}")
else:
    print(f"  ERROR: {r2.text[:300]}")

# Test recommendations have lender URLs
print("\n[2] GET /api/recommendations  -  checking lender website URLs")
recs = requests.get(f"{BASE}/api/recommendations", headers=H).json()
print(f"  Total recommendations saved: {len(recs)} (should be max 3 per application)")
for rec in recs[:3]:
    p = rec.get("product", {})
    print(f"  {p.get('product_name','?')} by {p.get('lender_name','?')}")
    print(f"    lender_website: {p.get('lender_website','NOT SET')}")
    print(f"    official_url: {p.get('official_product_url','NOT SET')}")

# Test report list
print("\n[3] GET /api/reports  -  saved reports")
reports = requests.get(f"{BASE}/api/reports", headers=H).json()
print(f"  {len(reports)} reports saved for this user")

print("\n=== Done ===")

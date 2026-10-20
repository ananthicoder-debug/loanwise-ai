"""
seed/seed_demo_showcase.py
---------------------------
Creates ONE fully-populated demo user with data across ALL features:
  - Complete personal + credit profile
  - Multiple loan applications (different categories)
  - Multiple active loans (one closed, one active with payments)
  - Full EMI schedule with PAID / OVERDUE / UPCOMING entries
  - Payment history
  - Documents (all types)
  - Notifications
  - Feedback
  - Admin logs

Demo User:
  Email:    demo@loanwise.ai
  Password: Demo@2026
  Name:     Arjun Mehta

Admin:
  Email:    admin@loanwise.ai
  Password: Admin@2026
"""

import sys, os
from pathlib import Path
from datetime import datetime, timedelta, timezone, date

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[1] / "ml"))

from bson import ObjectId
from database.mongodb import collections
from utils.security import hash_password
from services.recommendation_service import run_full_evaluation
from services.emi_service import generate_amortization_schedule


def _now():
    return datetime.now(timezone.utc)


def _days_ago(n):
    return datetime.now(timezone.utc) - timedelta(days=n)


def clear_demo_user():
    u = collections["users"].find_one({"email": "demo@loanwise.ai"})
    if u:
        uid = u["_id"]
        collections["credit_profiles"].delete_many({"user_id": uid})
        loan_apps = list(collections["loan_applications"].find({"user_id": uid}))
        app_ids = [a["_id"] for a in loan_apps]
        collections["predictions"].delete_many({"application_id": {"$in": app_ids}})
        collections["recommendations"].delete_many({"application_id": {"$in": app_ids}})
        loans = list(collections["active_loans"].find({"user_id": uid}))
        loan_oids = [l["_id"] for l in loans]
        collections["payments"].delete_many({"active_loan_id": {"$in": loan_oids}})
        collections["active_loans"].delete_many({"user_id": uid})
        collections["loan_applications"].delete_many({"user_id": uid})
        collections["documents"].delete_many({"user_id": uid})
        collections["notifications"].delete_many({"user_id": uid})
        collections["feedback"].delete_many({"user_id": uid})
        collections["users"].delete_one({"_id": uid})
        print("Cleared existing demo@loanwise.ai user.")


def create_demo_user():
    doc = {
        "full_name": "Arjun Mehta",
        "email": "demo@loanwise.ai",
        "phone": "9876543210",
        "password_hash": hash_password("Demo@2026"),
        "role": "user",
        "date_of_birth": "1992-07-15",
        "gender": "Male",
        "address": {
            "street": "42 Brigade Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001"
        },
        "pan_number": "ABCPM1234X",
        "status": "active",
        "created_at": _days_ago(90),
    }
    result = collections["users"].insert_one(doc)
    uid = result.inserted_id
    print(f"Created demo user: Arjun Mehta (demo@loanwise.ai)")
    return uid


def create_credit_profile(uid):
    cp = {
        "user_id": uid,
        "age": 32,
        "education": "Post Graduate",
        "employment_type": "Salaried",
        "employer_category": "IT/Tech",
        "years_of_employment": 8.5,
        "monthly_income": 85000,
        "annual_income": 1020000,
        "dependents": 1,
        "residence_type": "Rented",
        "residential_assets_value": 0,
        "commercial_assets_value": 0,
        "vehicle_owned": "Two Wheeler",
        "cibil_score": 748,
        "existing_loans": 1,
        "existing_emi": 7500,
        "outstanding_debt": 180000,
        "credit_card_outstanding": 25000,
        "credit_utilization": 0.18,
        "previous_loans": 3,
        "missed_payments": 0,
        "late_payments": 1,
        "average_days_late": 4.0,
        "coapplicant": False,
        "coapplicant_income": 0,
        # Legacy fields kept for compatibility
        "current_emi": 7500,
        "credit_history": "Good",
    }
    collections["credit_profiles"].insert_one(cp)
    print("Credit profile created: CIBIL=748, Income=Rs.85,000/month")
    return cp


def create_applications(uid, cp):
    """3 applications: Personal Loan (evaluated), Home Loan (evaluated), Vehicle Loan (evaluated)"""
    applications = []

    app_configs = [
        {
            "loan_amount": 500000,
            "loan_tenure": 36,
            "loan_category": "Personal Loan",
            "purpose": "Home renovation",
            "application_date": _days_ago(45),
            "status": "evaluated",
        },
        {
            "loan_amount": 3000000,
            "loan_tenure": 180,
            "loan_category": "Home Loan",
            "purpose": "Purchase",
            "application_date": _days_ago(20),
            "status": "evaluated",
        },
        {
            "loan_amount": 750000,
            "loan_tenure": 60,
            "loan_category": "Vehicle Loan",
            "purpose": "New car",
            "application_date": _days_ago(5),
            "status": "evaluated",
        },
    ]

    for cfg in app_configs:
        cfg["user_id"] = uid
        result = collections["loan_applications"].insert_one(cfg)
        cfg["_id"] = result.inserted_id
        applications.append(cfg)

    print(f"Created {len(applications)} loan applications")
    return applications


def run_evaluations(uid, applications, cp):
    """Run full ML evaluation for each application."""
    for app in applications:
        try:
            evaluation = run_full_evaluation(str(uid), app)
            print(f"  -> {app['loan_category']}: {evaluation['eligible_count']} eligible, "
                  f"{evaluation['recommended_count']} recommended")
        except Exception as e:
            print(f"  -> {app['loan_category']}: evaluation warning: {e}")


def create_active_loans(uid, applications):
    """
    Create 2 active loans from the Personal Loan application:
      Loan 1: CLOSED — all EMIs paid (6 months ago)
      Loan 2: ACTIVE — 12/36 EMIs done, 1 overdue
    """
    # Find a suitable Personal Loan product
    product = collections["loan_products"].find_one({"loan_category": "Personal Loan", "is_active": True})
    if not product:
        print("No Personal Loan product found — skipping active loans.")
        return []

    lender = collections["lenders"].find_one({"_id": product["lender_id"]})
    lender_name = lender["lender_name"] if lender else "Unknown"
    mid_rate = (product["interest_rate_min"] + product["interest_rate_max"]) / 2

    personal_app = next((a for a in applications if a["loan_category"] == "Personal Loan"), None)
    if not personal_app:
        return []

    created_loans = []

    # ── LOAN 1: CLOSED ──────────────────────────────────────────────────────
    start1 = _days_ago(365)
    first_due1 = start1 + timedelta(days=30)
    loan1_amount = 200000
    loan1_tenure = 12

    schedule1 = generate_amortization_schedule(
        loan1_amount, mid_rate, loan1_tenure, start1, first_due1
    )
    loan1_doc = {
        "user_id": uid,
        "product_id": product["_id"],
        "application_id": personal_app["_id"],
        "recommendation_id": None,
        "actual_amount": loan1_amount,
        "interest_rate": mid_rate,
        "tenure_months": loan1_tenure,
        "emi_amount": schedule1[0]["amount_due"],
        "start_date": start1.strftime("%Y-%m-%d"),
        "first_due_date": first_due1.strftime("%Y-%m-%d"),
        "status": "closed",
        "lender_name": lender_name,
        "created_at": start1,
    }
    res1 = collections["active_loans"].insert_one(loan1_doc)
    loan1_id = res1.inserted_id

    # Mark all 12 EMIs PAID
    for emi in schedule1:
        emi["active_loan_id"] = loan1_id
        emi["payment_status"] = "PAID"
        emi["amount_paid"] = emi["amount_due"]
        due_dt = datetime.strptime(emi["due_date"], "%Y-%m-%d")
        emi["payment_date"] = (due_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    collections["payments"].insert_many(schedule1)
    print(f"  Loan 1 CLOSED: Rs.{loan1_amount:,} Personal Loan — all 12 EMIs PAID")
    created_loans.append({"id": loan1_id, "status": "closed"})

    # ── LOAN 2: ACTIVE (12 of 36 done, EMI 13 OVERDUE) ──────────────────────
    start2 = _days_ago(400)
    first_due2 = start2 + timedelta(days=30)
    loan2_amount = 500000
    loan2_tenure = 36

    schedule2 = generate_amortization_schedule(
        loan2_amount, mid_rate, loan2_tenure, start2, first_due2
    )
    loan2_doc = {
        "user_id": uid,
        "product_id": product["_id"],
        "application_id": personal_app["_id"],
        "recommendation_id": None,
        "actual_amount": loan2_amount,
        "interest_rate": mid_rate,
        "tenure_months": loan2_tenure,
        "emi_amount": schedule2[0]["amount_due"],
        "start_date": start2.strftime("%Y-%m-%d"),
        "first_due_date": first_due2.strftime("%Y-%m-%d"),
        "status": "active",
        "lender_name": lender_name,
        "created_at": start2,
    }
    res2 = collections["active_loans"].insert_one(loan2_doc)
    loan2_id = res2.inserted_id

    for emi in schedule2:
        emi["active_loan_id"] = loan2_id

    # EMIs 1–11: PAID on time
    for emi in schedule2[:11]:
        emi["payment_status"] = "PAID"
        emi["amount_paid"] = emi["amount_due"]
        due_dt = datetime.strptime(emi["due_date"], "%Y-%m-%d")
        emi["payment_date"] = (due_dt + timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d") if True else due_dt.strftime("%Y-%m-%d")

    # EMI 12: PAID LATE (7 days late)
    emi12 = schedule2[11]
    emi12["payment_status"] = "PAID"
    emi12["amount_paid"] = emi12["amount_due"]
    due12 = datetime.strptime(emi12["due_date"], "%Y-%m-%d")
    emi12["payment_date"] = (due12 + timedelta(days=7)).strftime("%Y-%m-%d")
    emi12["days_overdue"] = 0
    emi12["late_charge"] = round(emi12["amount_due"] * 0.02, 2)

    # EMI 13: OVERDUE (set due date 12 days ago, unpaid)
    emi13 = schedule2[12]
    overdue_date = date.today() - timedelta(days=12)
    emi13["due_date"] = overdue_date.strftime("%Y-%m-%d")
    emi13["payment_status"] = "OVERDUE"
    emi13["days_overdue"] = 12
    emi13["late_charge"] = round(emi13["amount_due"] * 0.02, 2)

    # EMIs 14 onwards: UPCOMING
    collections["payments"].insert_many(schedule2)
    print(f"  Loan 2 ACTIVE: Rs.{loan2_amount:,} Personal Loan — 12 PAID, 1 OVERDUE, rest UPCOMING")
    created_loans.append({"id": loan2_id, "status": "active"})

    return created_loans


def create_documents(uid):
    docs = [
        {"document_type": "Identity Proof",   "file_name": "aadhaar_arjun_mehta.pdf",  "verification_status": "Verified",       "notes": "Aadhaar Card"},
        {"document_type": "Identity Proof",   "file_name": "pan_card_ABCPM1234X.pdf",  "verification_status": "Verified",       "notes": "PAN Card"},
        {"document_type": "Address Proof",    "file_name": "utility_bill_oct2025.pdf", "verification_status": "Verified",       "notes": "Electricity bill"},
        {"document_type": "Income Proof",     "file_name": "salary_slip_sep2025.pdf",  "verification_status": "Verified",       "notes": "Last 3 months salary slips"},
        {"document_type": "Bank Statement",   "file_name": "bank_stmt_6months.pdf",    "verification_status": "Pending Review", "notes": "SBI account — 6 months"},
        {"document_type": "Employment Proof", "file_name": "offer_letter_techcorp.pdf","verification_status": "Verified",       "notes": "Employment letter"},
    ]
    for doc in docs:
        doc["user_id"] = uid
        doc["upload_date"] = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        doc["created_at"] = _days_ago(30)
    collections["documents"].insert_many(docs)
    print(f"Created {len(docs)} documents")


def create_notifications(uid):
    notifs = [
        {
            "type": "emi_overdue",
            "title": "EMI Payment Overdue",
            "message": "Your EMI of Rs.18,870 was due 12 days ago. Please pay to avoid further late charges.",
            "is_read": False,
            "created_at": _days_ago(12),
        },
        {
            "type": "emi_reminder",
            "title": "Upcoming EMI Reminder",
            "message": "Your next EMI of Rs.18,870 is due in 7 days.",
            "is_read": False,
            "created_at": _days_ago(1),
        },
        {
            "type": "payment_confirmed",
            "title": "EMI Payment Confirmed",
            "message": "Your EMI payment of Rs.18,870 (EMI #11) has been marked as paid. Thank you!",
            "is_read": True,
            "created_at": _days_ago(32),
        },
        {
            "type": "eligibility_complete",
            "title": "Eligibility Check Completed",
            "message": "Your Home Loan eligibility check found 10 potentially matching products.",
            "is_read": True,
            "created_at": _days_ago(20),
        },
        {
            "type": "recommendation_ready",
            "title": "Loan Recommendations Ready",
            "message": "8 loan products appear both eligible and manageable for your current profile.",
            "is_read": False,
            "created_at": _days_ago(45),
        },
        {
            "type": "product_update",
            "title": "Catalogue Updated",
            "message": "The verified loan product catalogue has been updated with new products from IDFC FIRST Bank.",
            "is_read": False,
            "created_at": _days_ago(3),
        },
    ]
    for n in notifs:
        n["user_id"] = uid
    collections["notifications"].insert_many(notifs)
    print(f"Created {len(notifs)} notifications")


def create_feedback(uid):
    feedbacks = [
        {
            "user_id": uid,
            "rating": 5,
            "category": "Eligibility",
            "comments": "The eligibility check is very detailed. I could see exactly which products matched my profile and why.",
            "created_at": _days_ago(40),
        },
        {
            "user_id": uid,
            "rating": 4,
            "category": "EMI Calculator",
            "comments": "The amortisation schedule is very helpful for planning. Would love a graphical view.",
            "created_at": _days_ago(15),
        },
        {
            "user_id": uid,
            "rating": 5,
            "category": "Recommendations",
            "comments": "The recommendation explanation — especially the EMI-to-income ratio — was very clear and useful.",
            "created_at": _days_ago(7),
        },
    ]
    collections["feedback"].insert_many(feedbacks)
    print(f"Created {len(feedbacks)} feedback entries")


def create_admin_user():
    """Ensure admin exists with the right password."""
    collections["users"].delete_many({"email": "admin@loanwise.ai"})
    admin_doc = {
        "full_name": "System Administrator",
        "email": "admin@loanwise.ai",
        "phone": "9000000001",
        "password_hash": hash_password("Admin@2026"),
        "role": "admin",
        "date_of_birth": None,
        "gender": None,
        "address": {"street": "", "city": "Mumbai", "state": "Maharashtra", "pincode": ""},
        "status": "active",
        "created_at": _days_ago(180),
    }
    collections["users"].insert_one(admin_doc)
    print("Admin account: admin@loanwise.ai / Admin@2026")


def seed_admin_logs():
    """Seed sample admin activity logs for system logs page."""
    logs = [
        {"action": "LENDER_CATALOGUE_LOADED", "detail": "12 lenders loaded into MongoDB",         "admin": "System", "created_at": _days_ago(90)},
        {"action": "PRODUCT_CATALOGUE_LOADED", "detail": "62 products loaded into MongoDB",        "admin": "System", "created_at": _days_ago(90)},
        {"action": "MODEL_TRAINED",            "detail": "Model 1 (Eligibility) trained. F1=0.80", "admin": "System", "created_at": _days_ago(88)},
        {"action": "MODEL_TRAINED",            "detail": "Model 2 (Affordability) trained. F1=0.94","admin": "System","created_at": _days_ago(88)},
        {"action": "USER_REGISTERED",          "detail": "New user: Arjun Mehta",                  "admin": "System", "created_at": _days_ago(90)},
        {"action": "ELIGIBILITY_RUN",          "detail": "Personal Loan eligibility: 8 eligible",  "admin": "System", "created_at": _days_ago(45)},
        {"action": "ACTIVE_LOAN_CREATED",      "detail": "Loan Rs.5,00,000 created for Arjun Mehta","admin": "System", "created_at": _days_ago(40)},
        {"action": "PRODUCT_DEACTIVATED",      "detail": "Admin deactivated 1 old product",        "admin": "admin@loanwise.ai", "created_at": _days_ago(10)},
        {"action": "DATA_QUALITY_CHECK",       "detail": "Data quality check passed — 0 errors",   "admin": "admin@loanwise.ai", "created_at": _days_ago(5)},
        {"action": "DATASET_VERSION_SET",      "detail": "Dataset version 2.0 confirmed",          "admin": "System", "created_at": _days_ago(90)},
    ]
    collections["admin_logs"].delete_many({})
    collections["admin_logs"].insert_many(logs)
    print(f"Created {len(logs)} admin log entries")


import random

def main():
    print("\n" + "=" * 60)
    print("LoanWise AI — Demo Showcase Seed")
    print("=" * 60)

    # 1. Create admin
    create_admin_user()

    # 2. Clear + create demo user
    clear_demo_user()
    uid = create_demo_user()

    # 3. Credit profile
    cp = create_credit_profile(uid)

    # 4. Applications
    applications = create_applications(uid, cp)

    # 5. ML evaluations
    print("\nRunning ML evaluations...")
    run_evaluations(uid, applications, cp)

    # 6. Active loans
    print("\nCreating active loans...")
    create_active_loans(uid, applications)

    # 7. Documents
    create_documents(uid)

    # 8. Notifications
    create_notifications(uid)

    # 9. Feedback
    create_feedback(uid)

    # 10. Admin logs
    seed_admin_logs()

    # Summary
    print("\n" + "=" * 60)
    print("SHOWCASE SETUP COMPLETE")
    print("=" * 60)
    print()
    print("┌─────────────────────────────────────────────────┐")
    print("│            DEMO LOGIN CREDENTIALS               │")
    print("├─────────────────────────────────────────────────┤")
    print("│  DEMO USER                                      │")
    print("│  Email:    demo@loanwise.ai                     │")
    print("│  Password: Demo@2026                            │")
    print("│  Name:     Arjun Mehta                          │")
    print("├─────────────────────────────────────────────────┤")
    print("│  ADMIN                                          │")
    print("│  Email:    admin@loanwise.ai                    │")
    print("│  Password: Admin@2026                           │")
    print("├─────────────────────────────────────────────────┤")
    print("│  WHAT THE DEMO USER HAS:                        │")
    print("│  [OK] Complete personal + credit profile          │")
    print("│  [OK] 3 loan applications (PL, HL, VL)            │")
    print("│  [OK] ML eligibility + affordability results      │")
    print("│  [OK] Recommendations generated                   │")
    print("│  [OK] 1 CLOSED loan (12 EMIs all PAID)            │")
    print("│  [OK] 1 ACTIVE loan (12 PAID, 1 OVERDUE)          │")
    print("│  [OK] Full EMI schedule with payment history      │")
    print("│  [OK] 6 documents (identity, income, bank stmt)   │")
    print("│  [OK] 6 notifications (overdue, reminder, etc.)   │")
    print("│  [OK] 3 feedback entries                          │")
    print("├─────────────────────────────────────────────────┤")
    print("│  ADMIN CAN SEE:                                 │")
    print("│  [OK] All users with application counts           │")
    print("│  [OK] All loan applications                       │")
    print("│  [OK] ML prediction records                       │")
    print("│  [OK] Recommendation records                      │")
    print("│  [OK] 12 verified lenders                         │")
    print("│  [OK] 62 verified products                        │")
    print("│  [OK] Active + closed loans                       │")
    print("│  [OK] Full payment history                        │")
    print("│  [OK] Dataset version + collection counts         │")
    print("│  [OK] Data quality report                         │")
    print("│  [OK] Model performance metrics                   │")
    print("│  [OK] System activity logs                        │")
    print("│  [OK] User feedback                               │")
    print("└─────────────────────────────────────────────────┘")


if __name__ == "__main__":
    main()


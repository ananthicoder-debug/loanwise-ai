"""
seed/run_all_seeds.py
----------------------
Resets and populates the loan_ai_system database with:
  1. Verified Indian lenders (from lenders.csv)
  2. Verified Indian loan products (from loan_products.csv)
  3. Sample users (synthetic Indian profiles) + admin
  4. System metadata (dataset version info)
  5. A demo loan journey for the primary user

Run: python seed/run_all_seeds.py
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from bson import ObjectId

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))

from database.mongodb import collections
from seed.seed_lenders import seed_lenders
from seed.seed_products import seed_products
from seed.seed_users import seed_users
from services.recommendation_service import run_full_evaluation
from services.emi_service import generate_amortization_schedule


def seed_system_metadata():
    """Store dataset version metadata for the admin dashboard."""
    collections["system_metadata"].delete_many({"key": "dataset_version"})
    collections["system_metadata"].insert_one({
        "key": "dataset_version",
        "dataset_version": "2.0",
        "product_catalogue_version": "2026.09",
        "borrower_dataset_version": "india_v2",
        "historical_dataset_version": "repayment_v2",
        "updated_at": "2026-09-23",
        "description": "LoanWise AI — Verified Indian Loan Product Catalogue v2.0",
    })
    print("System metadata: version 2.0 written.")


def build_demo_journey():
    """
    Creates a complete demo loan journey for the primary demo user:
    - A Personal Loan application
    - Eligibility + Affordability evaluation
    - An active loan with EMI schedule
    - EMI #1 marked as PAID, EMI #2 left overdue
    """
    collections["loan_applications"].delete_many({})
    collections["predictions"].delete_many({})
    collections["recommendations"].delete_many({})
    collections["active_loans"].delete_many({})
    collections["payments"].delete_many({})
    collections["notifications"].delete_many({})
    collections["documents"].delete_many({})
    collections["feedback"].delete_many({})

    primary_user = collections["users"].find_one({"email": "anantha@example.com"})
    if not primary_user:
        print("Primary demo user not found — skipping demo journey.")
        return

    # Create a Personal Loan application
    application_doc = {
        "user_id": primary_user["_id"],
        "loan_amount": 500000,
        "loan_tenure": 36,
        "loan_category": "Personal Loan",
        "purpose": "Home renovation",
        "application_date": datetime.now(timezone.utc),
        "status": "evaluated",
    }
    result = collections["loan_applications"].insert_one(application_doc)
    application_doc["_id"] = result.inserted_id

    try:
        evaluation = run_full_evaluation(str(primary_user["_id"]), application_doc)
        print(
            f"Demo application: {evaluation['eligible_count']} eligible, "
            f"{evaluation['recommended_count']} recommended."
        )
    except Exception as e:
        print(f"Warning: evaluation failed ({e}). Skipping active loan creation.")
        return

    recommended = evaluation.get("recommended_products", [])
    if not recommended:
        print("No recommended products for demo profile — skipping active loan.")
        return

    chosen = recommended[0]
    start_date = datetime.now(timezone.utc) - timedelta(days=45)
    first_due_date = start_date + timedelta(days=15)

    schedule = generate_amortization_schedule(
        principal=application_doc["loan_amount"],
        annual_rate_percent=chosen["applied_interest_rate"],
        tenure_months=application_doc["loan_tenure"],
        start_date=start_date,
        first_due_date=first_due_date,
    )

    active_loan_doc = {
        "user_id": primary_user["_id"],
        "product_id": ObjectId(chosen["_id"]),
        "recommendation_id": ObjectId(chosen.get("recommendation_id")) if chosen.get("recommendation_id") else None,
        "application_id": application_doc["_id"],
        "actual_amount": application_doc["loan_amount"],
        "interest_rate": chosen["applied_interest_rate"],
        "tenure_months": application_doc["loan_tenure"],
        "emi_amount": schedule[0]["amount_due"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "first_due_date": first_due_date.strftime("%Y-%m-%d"),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
    }
    active_loan_result = collections["active_loans"].insert_one(active_loan_doc)

    for emi in schedule:
        emi["active_loan_id"] = active_loan_result.inserted_id
    collections["payments"].insert_many(schedule)

    # Mark EMI #1 as PAID
    collections["payments"].update_one(
        {"active_loan_id": active_loan_result.inserted_id, "emi_number": 1},
        {"$set": {
            "payment_status": "PAID",
            "amount_paid": schedule[0]["amount_due"],
            "payment_date": (first_due_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        }},
    )

    # Make EMI #2 visibly overdue in the review fixture.
    collections["payments"].update_one(
        {"active_loan_id": active_loan_result.inserted_id, "emi_number": 2},
        {"$set": {
            "payment_status": "OVERDUE",
            "due_date": (datetime.now(timezone.utc) - timedelta(days=15)).strftime("%Y-%m-%d"),
        }},
    )
    print(f"Demo active loan created. EMI: Rs.{schedule[0]['amount_due']:,.0f}/month for 36 months.")
    print("EMI #1: PAID | EMI #2: OVERDUE (past due) | Remaining: UPCOMING")

    # Seed a sample notification
    collections["notifications"].insert_one({
        "user_id": primary_user["_id"],
        "type": "emi_reminder",
        "title": "EMI Payment Reminder",
        "message": "Your EMI is overdue. Please make the payment to avoid late charges.",
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    })

    # Seed metadata-only documents and linked feedback so every user-facing
    # review page has representative data on the first login.
    collections["documents"].insert_many([
        {
            "user_id": primary_user["_id"],
            "document_type": "Identity Proof",
            "file_name": "anantha-pan-card.pdf",
            "notes": "PAN card submitted for identity verification.",
            "upload_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "verification_status": "Verified",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "user_id": primary_user["_id"],
            "document_type": "Income Proof",
            "file_name": "anantha-salary-slips.pdf",
            "notes": "Latest three salary slips.",
            "upload_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "verification_status": "Pending Review",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "user_id": primary_user["_id"],
            "document_type": "Address Proof",
            "file_name": "anantha-address-proof.pdf",
            "notes": "Current residential address proof.",
            "upload_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "verification_status": "Pending Review",
            "created_at": datetime.now(timezone.utc),
        },
    ])
    collections["feedback"].insert_one({
        "user_id": primary_user["_id"],
        "rating": 5,
        "category": "Recommendations",
        "comments": "The eligibility and repayment information was easy to understand.",
        "product_id": ObjectId(chosen["_id"]),
        "application_id": application_doc["_id"],
        "created_at": datetime.now(timezone.utc),
    })
    print("Demo documents: 3 seeded | Demo feedback: 1 seeded.")


def main():
    print("=" * 60)
    print("LoanWise AI — Database Setup")
    print("Database: loan_ai_system")
    print("=" * 60)

    seed_lenders()
    seed_products()
    seed_users()
    seed_system_metadata()
    build_demo_journey()

    print("=" * 60)
    print("Setup complete!")
    print("Login: anantha@example.com / Demo@123")
    print("Admin: admin@loanwise.ai / Admin@123")
    print("=" * 60)


if __name__ == "__main__":
    main()

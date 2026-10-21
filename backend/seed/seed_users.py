"""
seed/seed_users.py
---------------------
Creates sample Indian user profiles + 1 admin account.
All demo user passwords: Demo@123
Admin password: Admin@123

These are synthetic profiles for demonstration  -  not real people.
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from database.mongodb import collections
from utils.security import hash_password

# Realistic Indian profiles for demonstration
DEMO_USERS = [
    # full_name, email, dob, gender, city, state, phone
    # monthly_income, employment_type, employer_category, years_emp, dependents
    # cibil, existing_loans, existing_emi, outstanding_debt, prev_loans, missed, late, avg_days_late
    # education, residence_type, coapplicant
    (
        "Anantha Krishnan", "anantha@example.com", "1992-04-15", "Male", "Chennai", "Tamil Nadu", "9841234567",
        65000, "Salaried", "Private", 5.0, 1,
        760, 1, 6000, 150000, 2, 0, 1, 2.0,
        "Graduate", "Own", False
    ),
    (
        "Priya Sharma", "priya@example.com", "1995-08-22", "Female", "Mumbai", "Maharashtra", "9920012345",
        45000, "Salaried", "Private", 3.0, 0,
        700, 0, 0, 0, 0, 0, 0, 0.0,
        "Post Graduate", "Rented", False
    ),
    (
        "Ravi Kumar", "ravi@example.com", "1988-11-10", "Male", "Hyderabad", "Telangana", "9848011234",
        38000, "Self-Employed", "Self", 7.0, 2,
        640, 2, 9000, 300000, 3, 2, 3, 8.0,
        "Graduate", "Rented", False
    ),
    (
        "Sneha Reddy", "sneha@example.com", "1990-03-05", "Female", "Bengaluru", "Karnataka", "9886012345",
        90000, "Salaried", "IT/Tech", 8.0, 1,
        800, 0, 0, 0, 1, 0, 0, 0.0,
        "Post Graduate", "Own", True
    ),
    (
        "Arjun Verma", "arjun@example.com", "1998-07-18", "Male", "Delhi", "Delhi", "9911012345",
        28000, "Salaried", "Private", 2.0, 0,
        620, 0, 0, 0, 0, 1, 1, 3.0,
        "Graduate", "Rented", False
    ),
    (
        "Meena Iyer", "meena@example.com", "1985-12-25", "Female", "Coimbatore", "Tamil Nadu", "9843012345",
        55000, "Business Owner", "Self", 10.0, 3,
        670, 1, 7000, 200000, 2, 1, 2, 5.0,
        "Graduate", "Own", True
    ),
    (
        "Karthik Rajan", "karthik@example.com", "1987-09-14", "Male", "Pune", "Maharashtra", "9765012345",
        120000, "Salaried", "IT/Tech", 12.0, 2,
        820, 1, 5000, 100000, 3, 0, 0, 0.0,
        "Post Graduate", "Own", False
    ),
    (
        "Divya Nair", "divya@example.com", "1993-05-30", "Female", "Kochi", "Kerala", "9495012345",
        38000, "Salaried", "Government", 5.0, 0,
        690, 0, 0, 0, 1, 0, 1, 2.0,
        "Graduate", "Rented", False
    ),
    (
        "Suresh Babu", "suresh@example.com", "1982-01-08", "Male", "Visakhapatnam", "Andhra Pradesh", "9848902345",
        28000, "Self-Employed", "Self", 8.0, 4,
        610, 3, 11000, 400000, 4, 4, 5, 12.0,
        "12th", "Own", False
    ),
    (
        "Lakshmi Menon", "lakshmi@example.com", "1991-06-20", "Female", "Thiruvananthapuram", "Kerala", "9447012345",
        75000, "Salaried", "Government", 9.0, 1,
        745, 0, 3000, 50000, 2, 0, 0, 0.0,
        "Post Graduate", "Own", False
    ),
]


def seed_users():
    collections["users"].delete_many({"role": "user"})
    collections["users"].delete_many({"email": "admin@loanwise.ai"})
    collections["credit_profiles"].delete_many({})

    # Create admin account
    admin_doc = {
        "full_name": "System Administrator",
        "email": "admin@loanwise.ai",
        "phone": "9000000000",
        "password_hash": hash_password("Admin@123"),
        "role": "admin",
        "date_of_birth": None,
        "gender": None,
        "address": {"street": "", "city": "", "state": "", "pincode": ""},
        "status": "active",
        "created_at": datetime.now(timezone.utc),
    }
    collections["users"].insert_one(admin_doc)

    inserted = []
    for row in DEMO_USERS:
        (
            full_name, email, dob, gender, city, state, phone,
            monthly_income, emp_type, emp_category, years_emp, dependents,
            cibil, existing_loans, existing_emi, outstanding_debt, prev_loans, missed, late, avg_late,
            education, residence_type, coapplicant
        ) = row

        user_doc = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password_hash": hash_password("Demo@123"),
            "role": "user",
            "date_of_birth": dob,
            "gender": gender,
            "address": {
                "street": "Sample Address",
                "city": city,
                "state": state,
                "pincode": "600001"
            },
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
        result = collections["users"].insert_one(user_doc)

        collections["credit_profiles"].insert_one({
            "user_id": result.inserted_id,
            "age": int((datetime.now() - datetime.strptime(dob, "%Y-%m-%d")).days / 365.25),
            "education": education,
            "employment_type": emp_type,
            "employer_category": emp_category,
            "years_of_employment": years_emp,
            "monthly_income": monthly_income,
            "annual_income": monthly_income * 12,
            "dependents": dependents,
            "residence_type": residence_type,
            "cibil_score": cibil,
            "existing_loans": existing_loans,
            "existing_emi": existing_emi,
            "outstanding_debt": outstanding_debt,
            "credit_card_outstanding": 0,
            "credit_utilization": round(outstanding_debt / 300000, 2) if outstanding_debt else 0,
            "previous_loans": prev_loans,
            "missed_payments": missed,
            "late_payments": late,
            "average_days_late": avg_late,
            "coapplicant": coapplicant,
            "coapplicant_income": 0,
            # Legacy aliases for backward compatibility
            "current_emi": existing_emi,
            "credit_history": "Good" if cibil >= 700 else ("Average" if cibil >= 640 else "Poor"),
        })
        inserted.append((full_name, email))

    print(f"Users: {len(inserted)} sample users inserted + 1 admin")
    print("\nSample login credentials:")
    print("  Admin: admin@loanwise.ai / Admin@123")
    print(f"  User:  {inserted[0][1]} / Demo@123")
    return inserted


if __name__ == "__main__":
    seed_users()

"""
seed/seed_atlas.py
-------------------
Seeds the MongoDB Atlas database with lenders, products, users,
trained ML models metadata, and a demo loan journey.

Run after:
  1. Setting Atlas MONGODB_URI in .env
  2. Confirming connection: python test_atlas.py
  3. Training models: python ml/train_eligibility.py && python ml/train_affordability.py

Usage:
    cd backend
    python seed/seed_atlas.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.mongodb import check_connection, DATABASE_NAME, MONGODB_URI, IS_ATLAS

print("\n" + "=" * 60)
print("  LoanWise AI — Atlas Database Seeding")
print("=" * 60)
print(f"  Target: {'MongoDB Atlas' if IS_ATLAS else 'Local MongoDB'}")
print(f"  Database: {DATABASE_NAME}")
print()

if not IS_ATLAS:
    print("⚠️  WARNING: You are not connected to Atlas.")
    print("   Update MONGODB_URI in .env to use the Atlas connection string.")
    ans = input("   Seed local MongoDB anyway? (y/N): ").strip().lower()
    if ans != "y":
        print("   Aborted.")
        sys.exit(0)

if not check_connection():
    print("❌ Cannot connect to MongoDB. Check your connection string and network.")
    print("   Atlas: ensure your IP is whitelisted (Network Access → 0.0.0.0/0)")
    sys.exit(1)

print("  ✅ Connected. Starting seed...\n")

# Run the full seed
from seed.run_all_seeds import main
main()

# Also save trained model metrics to Atlas
print("\n  Saving model training metrics to Atlas...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))
    from model_utils import get_all_model_metadata
    records = get_all_model_metadata()
    print(f"  Model records in Atlas: {len(records)}")
except Exception as e:
    print(f"  Note: Model metrics not yet saved. Run training first: {e}")

print("\n" + "=" * 60)
print("  Atlas seeding complete!")
print(f"  View your data at: https://cloud.mongodb.com")
print("=" * 60 + "\n")

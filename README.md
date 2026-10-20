# LoanWise AI
## Intelligent Indian Loan Eligibility, Recommendation and Repayment Management System

**Motto:** "Know what you may qualify for. Understand what you can manage. Choose with clarity. Repay with confidence."  
**Tagline:** "From Eligibility to Repayment — One Intelligent Loan Journey."

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI 0.111, Uvicorn |
| Database | MongoDB 6.0+ via PyMongo 4.7 |
| ML | scikit-learn 1.5, pandas 2.2, numpy 1.26, joblib |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Frontend | HTML5, Bootstrap 5.3.3, jQuery 3.7.1, Chart.js 4.4.4 |

---

## Project Structure

```
LoanWise AI/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── .env                       # Environment variables
│   ├── requirements.txt
│   ├── database/mongodb.py        # MongoDB connection + all collections
│   ├── models/                    # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── loan.py
│   │   └── payment.py
│   ├── routes/                    # All API endpoints
│   │   ├── auth.py                # POST /api/auth/register, /login
│   │   ├── users.py               # GET/PUT /api/users/profile
│   │   ├── credit.py              # GET/PUT /api/credit-profile
│   │   ├── loans.py               # GET /api/loans, /categories, /lenders, /search, /compare
│   │   ├── applications.py        # POST/GET /api/applications
│   │   ├── predictions.py         # POST /api/predictions/eligibility, /affordability
│   │   ├── recommendations.py     # GET /api/recommendations
│   │   ├── active_loans.py        # POST/GET /api/active-loans
│   │   ├── payments.py            # GET schedule, POST mark-paid
│   │   ├── notifications.py       # GET/PUT /api/notifications
│   │   ├── documents.py           # GET/POST/DELETE /api/documents
│   │   ├── feedback.py            # GET/POST /api/feedback
│   │   ├── dashboard.py           # GET /api/dashboard
│   │   ├── admin.py               # All /api/admin/* endpoints
│   │   └── datasets.py            # GET /api/admin/datasets, /data-quality
│   ├── services/                  # Business logic
│   │   ├── eligibility_service.py # Model 1 + product rule matching
│   │   ├── affordability_service.py # Model 2 evaluation
│   │   ├── recommendation_service.py # Eligible ∩ Manageable = Recommended
│   │   ├── emi_service.py         # EMI formula + amortisation schedule
│   │   ├── notification_service.py # EMI reminders + overdue detection
│   │   └── product_service.py     # Product catalogue helpers
│   ├── ml/                        # Machine learning pipeline
│   │   ├── train_eligibility.py   # Train Model 1 (LogisticRegression)
│   │   ├── train_affordability.py # Train Model 2 (LogisticRegression)
│   │   ├── predict_eligibility.py # Model 1 inference
│   │   ├── predict_affordability.py # Model 2 inference
│   │   ├── preprocessing.py       # Feature definitions shared by train+predict
│   │   └── models/                # Trained .joblib files
│   ├── services/                  # Business logic
│   │   ├── eligibility_service.py
│   │   ├── affordability_service.py
│   │   ├── recommendation_service.py
│   │   ├── assessment_service.py  # NEW: full two-model assessment with explainability
│   │   ├── calculation_service.py # NEW: calculation worksheet + traces
│   │   ├── explainability_service.py # NEW: feature importance, factor analysis
│   │   ├── report_service.py
│   │   ├── emi_service.py
│   │   └── product_service.py
│   ├── routes/
│   │   ├── assessment.py          # NEW: POST /api/assessment/full/{id}, what-if
│   │   ├── documents.py           # UPDATED: real file upload + admin verification
│   │   └── ... (existing routes unchanged)
│   └── uploads/documents/         # NEW: uploaded document files stored here
│   ├── seed/                      # Database setup scripts
│   │   ├── run_all_seeds.py       # ← Run this first (full setup)
│   │   ├── seed_lenders.py        # Import verified Indian lenders
│   │   ├── seed_products.py       # Import verified loan products
│   │   ├── seed_users.py          # Create demo users + admin
│   │   ├── import_historical_loans.py  # Import synthetic historical data
│   │   └── import_payments.py         # Import synthetic payment records
│   └── data/raw/                  # CSV datasets
│       ├── lenders.csv            # 12 verified Indian lenders
│       ├── loan_products.csv      # 62 verified loan products
│       ├── borrowers.csv          # 5,000 synthetic borrower profiles
│       ├── eligibility_dataset.csv # ML training data
│       ├── affordability_dataset.csv # ML training data
│       ├── historical_loans.csv   # 10,000 synthetic loan records
│       └── installment_payments.csv # 60,000 synthetic payment records
└── frontend/                      # Static HTML/CSS/JS (no Node.js, no React)
    ├── index.html                 # Landing page
    ├── login.html / register.html
    ├── dashboard.html
    ├── profile.html               # Personal + employment + financial + credit tabs
    ├── financial-health.html      # Financial obligation summary
    ├── loan-categories.html       # Browse by category (counts from MongoDB)
    ├── lenders.html               # Lender directory (no ranking)
    ├── loan-search.html           # Search by name/lender/category
    ├── eligible-loans.html        # Eligibility check + results
    ├── recommended-loans.html     # Model 1 ∩ Model 2 recommendations
    ├── loan-details.html          # Product detail + quick EMI calc
    ├── compare-loans.html         # Side-by-side comparison (2–4 products)
    ├── emi-calculator.html        # Full EMI + amortisation schedule
    ├── verified-products.html     # Complete verified catalogue
    ├── applications.html          # Application history
    ├── active-loans.html          # My active loans
    ├── emi-schedule.html          # Per-loan EMI schedule with Mark Paid
    ├── payment-history.html       # All payment records
    ├── notifications.html         # EMI reminders + overdue alerts
    ├── documents.html             # Document metadata tracker
    ├── feedback.html              # Feedback form
    ├── admin-dashboard.html       # Admin overview + charts
    ├── admin-users.html           # User management
    ├── admin-applications.html    # All applications
    ├── admin-lenders.html         # Lender management (CRUD)
    ├── admin-products.html        # Product management (deactivate)
    ├── admin-predictions.html     # All ML prediction records
    ├── admin-recommendations.html # All recommendation records
    ├── admin-active-loans.html    # All active loans
    ├── admin-payments.html        # All payment records
    ├── admin-datasets.html        # Live collection counts + version info
    ├── admin-data-quality.html    # Catalogue validation report
    ├── admin-feedback.html        # All user feedback
    ├── css/style.css              # Unified stylesheet
    └── js/
        ├── common.js              # API, auth, sidebar, formatting
        ├── auth.js                # Login + register
        ├── dashboard.js           # User dashboard + charts
        ├── profile.js             # 4-tab profile page
        ├── loans.js               # Eligible loans + search
        ├── recommendations.js     # Recommended loans
        ├── active-loans.js        # Loan details + active loans
        ├── payments.js            # EMI schedule + payment history
        ├── emi.js                 # EMI calc + compare + financial health
        ├── notifications.js       # Notifications + applications + documents + feedback
        ├── datasets.js            # Verified products catalogue
        └── admin.js               # All admin page functions
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- MongoDB 6.0+ installed (the app manages starting it — see Step 1)
- A modern browser (Chrome/Firefox/Edge)

### Step 1 — Start MongoDB

**Option A (Recommended): Double-click `START_LOANWISE.bat`** — starts MongoDB, seeds the DB, and launches the backend automatically.

**Option B: Manual MongoDB start**
```bat
REM From the LoanAssist-AI\LoanAssist-AI\ directory:
START_MONGODB.bat
```

Or using PowerShell (replace with your mongod path if different):
```powershell
$mongod = "C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe"
Start-Process -FilePath $mongod -ArgumentList "--config", "C:\data\mongod.cfg" -WindowStyle Hidden
```

The MongoDB config at `C:\data\mongod.cfg` is created automatically by the startup scripts.

**Note for MongoDB 8.3 on Windows:** If MongoDB crashes immediately, it's a known FTDC bug. The `C:\data\mongod.cfg` includes `diagnosticDataCollectionEnabled: false` to prevent this.

### Step 2 — Configure Environment

The `backend/.env` file is already configured:
```
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=loan_ai_system
JWT_SECRET=loanwise_ai_secret_key_2026_change_before_deployment
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Step 3 — Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 4 — Train ML Models

```bash
python ml/train_eligibility.py
python ml/train_affordability.py
```

Both models train on the 5,000-record synthetic datasets and save to `ml/models/`.

**Actual training results (verified):**

| Model | Algorithm | Records | Accuracy | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Eligibility | LogisticRegression | 4000 train / 1000 test | 76.4% | 0.82 | 0.83 |
| Affordability | LogisticRegression | 4000 train / 1000 test | 82.6% | 0.70 | 0.92 |

- Eligibility target: `loan_status` (61.8% Eligible, 38.2% Not Eligible)
- Affordability target: `manageable` (22.5% Manageable — class imbalance handled with `class_weight=balanced`)

**Run both models in one command:**
```bash
python -m ml.train_eligibility
python -m ml.train_affordability
```

### Step 5 — Start the Backend

```bash
uvicorn main:app --reload
```

- API: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### Step 6 — Open the Frontend

Open `frontend/index.html` directly in a browser, or use VS Code Live Server (recommended).

Or serve with Python:
```bash
cd frontend
python -m http.server 5500
```
Then open `http://localhost:5500`

## Starting the Application

### Easiest method — 2 steps

**Step 1: Start MongoDB + Backend** — double-click `START_LOANWISE.bat`

**Step 2: Open the App** — double-click `OPEN_APP.bat` (or open `LoanAssist-AI/frontend/index.html` directly in Chrome)

---

### Frontend server (optional — only needed if direct file open has issues)

Port 5500 may be blocked by other software (e.g. Oracle TNS Listener).
Use `START_FRONTEND.bat` which auto-detects a free port:

```
START_FRONTEND.bat
```

Then open: `http://localhost:5501/index.html` (or whichever port it picks)

---

### Manual startup

```powershell
# Terminal 1 — Start MongoDB
$m = "C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe"
Start-Process -FilePath $m -ArgumentList "--config","C:\data\mongod.cfg"
Start-Sleep 8

# Terminal 1 — Backend
cd LoanAssist-AI\LoanAssist-AI\backend
pip install -r requirements.txt
python seed/run_all_seeds.py
python ml/train_eligibility.py
python ml/train_affordability.py
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open `LoanAssist-AI\LoanAssist-AI\frontend\index.html` in your browser.

### Troubleshooting port errors

| Error | Cause | Fix |
|---|---|---|
| `[WinError 10013]` on port 5500 | Oracle TNS Listener or another service | Use `START_FRONTEND.bat` or open HTML directly |
| `[WinError 10061]` MongoDB refused | MongoDB not running | Run `START_MONGODB.bat` |
| `ServerSelectionTimeoutError` | MongoDB stopped | Run `START_MONGODB.bat` |
| "Cannot reach backend" in browser | uvicorn not started | Run `START_LOANWISE.bat` |

| Account | Email | Password | What it demonstrates |
|---|---|---|---|
| Review user | `anantha@example.com` | `Demo@123` | Profile, credit data, eligibility, recommendations, comparison, EMI calculation, application history, active loan, payment schedule, notifications, documents, and feedback |
| Review admin | `admin@loanwise.ai` | `Admin@123` | All admin dashboards and catalogue/data management screens |

The seeded user has one evaluated Personal Loan application, 8 eligible products, 8 recommendations, one active 36-month loan, one paid EMI, upcoming payments, an EMI notification, three document records, and one feedback record. The seed can be rerun whenever a clean review database is needed.

### Admin Review Capabilities

Use the admin account to explain the system from the operations side:

| Admin screen | Capability to demonstrate |
|---|---|
| Dashboard | System totals, applications by category, products by lender, payment status, overdue count |
| Users | Browse users and application counts; activate or deactivate a user |
| Applications | Review every applicant's loan request and status |
| Lenders | Create, edit, list, and deactivate lenders |
| Products | Create, edit, list, and deactivate loan products |
| Predictions | Inspect stored eligibility and affordability prediction results |
| Recommendations | Inspect model-based product recommendations and match scores |
| Active Loans | Monitor every active loan, borrower, lender, and product |
| Payments | Review EMI schedules, payment status, due dates, and amounts |
| Datasets | View collection counts and dataset version metadata |
| Data Quality | Validate the verified lender and product catalogue |
| Feedback | Review ratings and comments submitted by users |

### API Smoke Checks

With the backend running, these URLs are useful during the review:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/docs
http://localhost:5500/login.html
```

---

## Default Login Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@loanwise.ai | Admin@123 |
| User | anantha@example.com | Demo@123 |
| User | priya@example.com | Demo@123 |
| User | ravi@example.com | Demo@123 |
| User | sneha@example.com | Demo@123 |

---

## Machine Learning Models

### Model 1 — Loan Eligibility Prediction

| Property | Value |
|---|---|
| Algorithm | Logistic Regression |
| Training Data | 5,000 synthetic records (`eligibility_dataset.csv`) |
| Training / Test Split | 4,000 / 1,000 (stratified) |
| Target Column | `loan_status` (0=Not Eligible, 1=Eligible) |
| Class Distribution | 61.8% Eligible / 38.2% Not Eligible |
| Features | Age, Annual Income, Education, Employment Type, Dependents, CIBIL Score, Existing Loans, Outstanding Debt, Requested Amount, Requested Tenure |
| Feature Count | 10 |
| Accuracy | 76.4% |
| F1 Score | 0.82 |
| ROC-AUC | 0.83 |
| Output | `Eligible` / `Not Eligible` + probability |
| File | `ml/models/eligibility_model.joblib` |

### Model 2 — Loan Affordability and Repayment Feasibility

| Property | Value |
|---|---|
| Algorithm | Logistic Regression |
| Training Data | 5,000 synthetic records (`affordability_dataset.csv`) |
| Training / Test Split | 4,000 / 1,000 (stratified) |
| Target Column | `manageable` (0=Not Manageable, 1=Manageable) |
| Class Distribution | 22.5% Manageable — **imbalanced** — mitigated with `class_weight=balanced` |
| Features | Monthly Income, Dependents, Existing Loans, Current EMI, Outstanding Debt, Previous Loans, Missed Payments, Late Payments, Proposed Amount, Proposed Rate, Proposed Tenure, Proposed EMI, EMI-to-Income Ratio |
| Feature Count | 13 |
| Accuracy | 82.6% |
| F1 Score | 0.70 |
| ROC-AUC | 0.92 |
| Output | `Manageable` / `Not Manageable` + probability |
| File | `ml/models/affordability_model.joblib` |

### Model Limitations

- Both models trained on **synthetic data** — not real bank decisions or real repayment records.
- Model 1 F1=0.82 reflects the synthetic label quality; real lender approval rules differ.
- Model 2 ROC-AUC=0.92 is high but driven by the strong `emi_income_ratio` feature which is deterministic.
- These metrics do NOT imply the models work for real loan applications.

### Recommendation Engine (Rule-Based, NOT a third ML model)

```
Eligible Products (Model 1) ∩ Manageable Products (Model 2) = Recommended
```

Match score = `(Model1_probability × 0.5 + Model2_probability × 0.5) × 100`

---

## Data Types — Important Distinction

| Type | Description | Label in App |
|---|---|---|
| Verified Product Catalogue | Real Indian lenders + real loan products from official pages | ✅ Verified |
| Synthetic Borrower Data | 5,000 synthetic profiles for ML training only | Synthetic Training Data |
| Synthetic Historical Data | Synthetic repayment records for demo | Synthetic Historical Data |

---

## Verified Lenders

All 12 lenders are real Indian banks/NBFCs with official website URLs:

| Code | Lender | Type |
|---|---|---|
| L001 | State Bank of India | Bank |
| L002 | HDFC Bank | Bank |
| L003 | ICICI Bank | Bank |
| L004 | Axis Bank | Bank |
| L005 | Punjab National Bank | Bank |
| L006 | Bank of Baroda | Bank |
| L007 | Canara Bank | Bank |
| L008 | Kotak Mahindra Bank | Bank |
| L009 | IDFC FIRST Bank | Bank |
| L010 | IndusInd Bank | Bank |
| L011 | Bajaj Finance | NBFC |
| L012 | Tata Capital | NBFC |

---

## API Reference

Base URL: `http://127.0.0.1:8000`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account, returns JWT |
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/me` | Current user info |

### User
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users/profile` | Personal profile |
| PUT | `/api/users/profile` | Update personal profile |
| GET | `/api/credit-profile` | Financial/credit profile |
| PUT | `/api/credit-profile` | Update financial profile |

### Loans
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/loans` | Full catalogue grouped by category → lender |
| GET | `/api/loans/categories` | Categories with product/lender counts |
| GET | `/api/loans/lenders` | Lender list with product counts |
| GET | `/api/loans/lenders/{id}` | Single lender + their products |
| GET | `/api/loans/search?q=` | Search by name/lender/category |
| GET | `/api/loans/compare?ids=` | Compare 2–4 products |
| GET | `/api/loans/{id}` | Single product detail |

### Applications & ML
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/applications` | Submit requirement → runs both models |
| GET | `/api/applications` | My application history |
| GET | `/api/applications/{id}` | Re-fetch application results |
| GET | `/api/recommendations` | My recommended products |
| POST | `/api/predictions/eligibility` | Model 1 only |
| POST | `/api/predictions/affordability` | Model 1 + Model 2 |

### Loan Management
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/active-loans` | Create active loan + EMI schedule |
| GET | `/api/active-loans` | My active loans |
| GET | `/api/active-loans/{id}` | Single active loan |
| GET | `/api/active-loans/{id}/payments` | EMI schedule |
| POST | `/api/payments/{id}/mark-paid` | Mark EMI as paid |

### Misc
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/notifications` | EMI reminders + system alerts |
| PUT | `/api/notifications/{id}/read` | Mark notification read |
| GET | `/api/documents` | My documents |
| POST | `/api/documents` | Add document entry |
| GET | `/api/feedback` | My feedback |
| POST | `/api/feedback` | Submit feedback |
| GET | `/api/dashboard` | User dashboard data |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/dashboard` | System overview + charts |
| GET | `/api/admin/users` | All users |
| PUT | `/api/admin/users/{id}/status` | Toggle user active/inactive |
| GET | `/api/admin/applications` | All applications |
| GET | `/api/admin/predictions` | All ML predictions |
| GET | `/api/admin/recommendations` | All recommendations |
| GET/POST | `/api/admin/lenders` | List / Add lender |
| PUT/DELETE | `/api/admin/lenders/{id}` | Edit / Deactivate lender |
| GET/POST | `/api/admin/products` | List / Add product |
| PUT/DELETE | `/api/admin/products/{id}` | Edit / Deactivate product |
| GET | `/api/admin/active-loans` | All active loans |
| GET | `/api/admin/payments` | All payment records |
| GET | `/api/admin/feedback` | All user feedback |
| GET | `/api/admin/datasets` | Live collection counts + version |
| GET | `/api/admin/data-quality` | Catalogue validation report |
| GET | `/api/admin/lender-stats` | Products per lender aggregation |
| GET | `/api/admin/category-stats` | Products per category aggregation |

Full interactive docs: `http://127.0.0.1:8000/docs`

---

## User Journey

```
Landing Page → Register → Login
→ Dashboard → Profile (4 tabs) → Financial Health
→ Loan Categories → Lender Directory → Search Loans
→ Enter Loan Requirement → Run Model 1 (Eligibility)
→ View Eligible Products (Category → Lender → Product hierarchy)
→ Run Model 2 (Affordability) → View Recommendations
→ Product Details → Compare Products → EMI Calculator
→ Consider Loan → Active Loan Created → EMI Schedule
→ Mark Payments → Payment History → Notifications
→ Documents → Feedback
```

---

## Key Design Decisions

1. **No hardcoded counts** — all statistics are live MongoDB aggregation queries
2. **Products never hidden** — ALL products shown, each marked Eligible or Not Eligible
3. **Model output separated from catalogue data** — clearly labelled in UI
4. **Recommendation = rule engine** — intersection of Model 1 and Model 2, not a third ML model
5. **No Node.js, no React** — plain HTML/CSS/JS with Bootstrap + jQuery
6. **EMI formula** — standard reducing-balance: `EMI = P × r × (1+r)^n / ((1+r)^n - 1)`
7. **No mock fallbacks** — if MongoDB is empty, shows empty state, never fake data

---

## New Features Added (v2.1 — Current)

### Full Assessment Report (`assessment-report.html`)
After checking eligibility, click **📊 Full Report** to get a complete two-model explainability report including:
- Model 1 & 2 predictions with confidence percentages, input features, and factor analysis
- Step-by-step financial calculation worksheet (EMI, ETI ratio, surplus, DTI)
- Historical repayment analysis from credit profile
- Eligible vs Recommended products (always separate, eligible products never hidden)
- What-If scenario calculator — adjust amount/rate/tenure, recalculates without changing saved application

### Document Upload with Admin Verification
Users upload actual government-issued documents (PDF/JPG/PNG/DOC/DOCX, max 10 MB each). Admins review and verify/reject each document to confirm repayment capability.
- Upload: `POST /api/documents/upload`
- Admin verification page: `admin-documents.html`

### Test Suite
```bash
cd backend
python tests/test_full_system.py
```
13 automated tests — all passing.

---

## Academic Disclaimer

This is an academic prototype built for educational purposes:
- Document upload is **functional file storage** — files stored in `backend/uploads/documents/`
- EMI calculations are **estimates** — actual terms set by lenders
- No real financial transactions occur
- Not suitable for production without significant additional work

All AI model outputs are clearly labelled as estimates, not guaranteed lender approvals.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Unable to connect to the backend" | Run `uvicorn main:app --reload` from `backend/` |
| "ServerSelectionTimeoutError" | Start MongoDB Community Server |
| "No loan products in catalogue" | Run `python seed/run_all_seeds.py` |
| "No credit profile" error | Complete profile on `profile.html` first |
| Bcrypt version warning | Cosmetic only — auth still works |
| CORS error in browser | Make sure backend is running on port 8000 |

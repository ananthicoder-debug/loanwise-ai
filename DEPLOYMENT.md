# LoanWise AI — Deployment Guide

## Current Status

| Component | Status | Details |
|---|---|---|
| MongoDB Atlas | CONNECTED | cluster0.ckt9xiq.mongodb.net |
| Database | SEEDED | 12 lenders, 62 products, 11 users |
| Model 1 | TRAINED | LogReg, F1=0.82, ROC-AUC=0.83 |
| Model 2 | TRAINED | LogReg, F1=0.70, ROC-AUC=0.92 |
| Backend | RUNNING | http://localhost:8000 |
| Tests | PASSING | 13/13 |

---

## Architecture

```
Frontend (HTML/CSS/JS)         Backend (FastAPI)           Database
  Local file / Netlify    →→→  Render.com (free)  →→→  MongoDB Atlas
  GitHub Pages                 Railway                   (connected)
```

---

## Running Locally (Current Setup)

### 1. Start the backend
```bat
START_LOANWISE.bat
```
Backend auto-connects to Atlas. No local MongoDB needed.

### 2. Open the frontend
```bat
OPEN_APP.bat
```
Or run: `python -m http.server 5502` inside `LoanAssist-AI\frontend\`
Then open: http://localhost:5502/index.html

### 3. Login
- User: anantha@example.com / Demo@123
- Admin: admin@loanwise.ai / Admin@123

---

## Deploy Backend to Render.com (Free)

### Step 1 — Push to GitHub

```bash
cd C:\Users\Admin\Downloads\LoanAssist-AI\LoanAssist-AI
git init
git add .
git commit -m "LoanWise AI - deploy"
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/loanwise-ai.git
git push -u origin main
```

### Step 2 — Create Render Web Service

1. Go to https://render.com → Sign up free
2. New → Web Service → Connect your GitHub repo
3. Settings:

| Setting | Value |
|---|---|
| Name | loanwise-ai-backend |
| Root Directory | LoanAssist-AI/backend |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt && python ml/train_eligibility.py && python ml/train_affordability.py && python seed/run_all_seeds.py` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free |

### Step 3 — Set Environment Variables in Render

Go to: Render Dashboard → Your Service → Environment → Add variables

| Key | Value |
|---|---|
| MONGODB_URI | mongodb+srv://ananthavalliuofficial_db_user:nraXeFPEfhtvTuxC@cluster0.ckt9xiq.mongodb.net/loan_ai_system?retryWrites=true&w=majority&appName=Cluster0 |
| DATABASE_NAME | loan_ai_system |
| JWT_SECRET | loanwise_ai_jwt_secret_ananthavalli_2026_production |
| JWT_ALGORITHM | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 1440 |
| APP_ENV | production |

Click Deploy Service — takes ~5 minutes.

Your backend URL: https://loanwise-ai-backend.onrender.com

### Step 4 — Update frontend config

Edit: `LoanAssist-AI/frontend/js/config.js`
```javascript
const PROD_API_URL = "https://loanwise-ai-backend.onrender.com";
```

### Step 5 — Test deployed backend
Open: https://loanwise-ai-backend.onrender.com/api/health
Should return: {"status":"ok","connection_type":"atlas","mongodb":"connected"}

---

## Deploy Frontend to Netlify (Free)

### Option A — Drag and Drop (Easiest)
1. Go to https://netlify.com → Log in → New site
2. Drag the entire `LoanAssist-AI/frontend/` folder
3. Done — you get a URL like https://loanwise-ai.netlify.app

### Option B — From GitHub
1. Netlify → New site from Git → GitHub → select repo
2. Base directory: LoanAssist-AI/frontend
3. Build command: (leave empty)
4. Publish directory: LoanAssist-AI/frontend
5. Deploy

---

## MongoDB Atlas — Important Settings

### Network Access
1. Atlas Dashboard → Network Access
2. Add IP Address → Allow Access from Anywhere (0.0.0.0/0)
   Required for Render.com (dynamic IPs)

### MongoDB Compass (local GUI)
1. Open MongoDB Compass
2. New Connection → paste:
   mongodb+srv://ananthavalliuofficial_db_user:nraXeFPEfhtvTuxC@cluster0.ckt9xiq.mongodb.net/
3. Connect → select loan_ai_system database

---

## Switch Between Atlas and Local

```bat
REM Use Atlas (production):
USE_ATLAS.bat

REM Use local MongoDB (offline development):
USE_LOCAL.bat
```

---

## Switching .env Files Reference

| File | Database | Use when |
|---|---|---|
| .env | Currently active config | Loaded by the app |
| .env.production | MongoDB Atlas | Production / deployment |
| .env.local | Local MongoDB | Offline development |
| .env.example | Template (safe to commit) | Reference |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Atlas auth failed | Check username/password in .env |
| Atlas timeout | Whitelist 0.0.0.0/0 in Atlas Network Access |
| Port 5500 blocked | Use port 5502: `python -m http.server 5502` |
| Port 5501 blocked | Use port 5502 (5501 also taken by Oracle TNS) |
| CORS error | Add frontend URL to allow_origins in main.py |
| Render build fails | Check build logs, ensure requirements.txt is complete |
| Atlas free tier paused | Log into Atlas and unpause the cluster |
| Name not updating in sidebar | Fixed in profile.js - localStorage syncs immediately |

---

## Atlas Cluster Details

```
Cluster:    cluster0.ckt9xiq.mongodb.net
Database:   loan_ai_system
Username:   ananthavalliuofficial_db_user
Region:     Auto (free tier)
Plan:       M0 Free
```

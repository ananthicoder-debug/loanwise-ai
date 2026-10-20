@echo off
title LoanWise AI — Application Startup
chcp 65001 > nul
echo.
echo ============================================================
echo   LoanWise AI — Intelligent Indian Loan Platform
echo ============================================================
echo.

REM The backend folder is next to this .bat file
set BACKEND=%~dp0backend
cd /d "%BACKEND%"

REM Verify we are in the right place
if not exist "main.py" (
    echo.
    echo   [ERROR] Cannot find main.py in: %BACKEND%
    echo   Make sure this .bat file is in the LoanAssist-AI folder
    echo   next to the 'backend' directory.
    echo.
    pause
    exit /b 1
)

echo   Backend directory: %BACKEND%
echo.

REM ── Detect mode (Atlas vs Local) ─────────────────────────────
findstr /C:"mongodb+srv" .env > nul 2>&1
if %ERRORLEVEL%==0 (
    echo   Database: MongoDB Atlas (cloud)
    goto :step2
)
echo   Database: Local MongoDB

REM ── Start local MongoDB only if needed ───────────────────────
netstat -an 2>nul | findstr ":27017 " > nul
if %ERRORLEVEL%==0 (
    echo   [OK] Local MongoDB already running
    goto :step2
)
echo   Starting local MongoDB...
if not exist "C:\data\db" mkdir "C:\data\db"
if not exist "C:\data\mongod.cfg" (
    (
        echo storage:
        echo   dbPath: C:\data\db
        echo systemLog:
        echo   destination: file
        echo   logAppend: true
        echo   path: C:\data\mongod.log
        echo net:
        echo   port: 27017
        echo   bindIp: 127.0.0.1
        echo setParameter:
        echo   diagnosticDataCollectionEnabled: false
    ) > "C:\data\mongod.cfg"
)
start "MongoDB" /min "C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe" --config "C:\data\mongod.cfg"
timeout /t 8 /nobreak > nul

:step2
REM ── Python dependencies ──────────────────────────────────────
echo.
echo [1/3] Checking dependencies...
pip install -r requirements.txt -q --disable-pip-version-check 2>nul
echo   [OK] Dependencies ready

REM ── Seed database if empty (first run) ───────────────────────
echo.
echo [2/3] Checking database...
python -c "
import sys
sys.path.insert(0, '.')
try:
    from database.mongodb import collections
    n = collections['lenders'].count_documents({})
    sys.exit(0 if n >= 12 else 1)
except:
    sys.exit(1)
" 2>nul
if %ERRORLEVEL%==1 (
    echo   First run — seeding database...
    python seed/run_all_seeds.py
    echo   Training ML models (this takes ~1 minute)...
    python ml/train_eligibility.py > nul 2>&1
    python ml/train_affordability.py > nul 2>&1
    echo   [OK] Database seeded and models trained
) else (
    echo   [OK] Database already has data
)

REM ── Start FastAPI backend ─────────────────────────────────────
echo.
echo [3/3] Starting LoanWise AI backend...
echo.
echo ============================================================
echo.
echo   BACKEND:   http://localhost:8000
echo   API DOCS:  http://localhost:8000/docs
echo   HEALTH:    http://localhost:8000/api/health
echo.
echo   To open the app, run OPEN_APP.bat or:
echo   Open frontend\index.html in your browser
echo.
echo   LOGIN:     anantha@example.com  /  Demo@123
echo   ADMIN:     admin@loanwise.ai    /  Admin@123
echo.
echo ============================================================
echo.
echo   Press Ctrl+C to stop the backend.
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

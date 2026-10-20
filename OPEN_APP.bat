@echo off
title LoanWise AI — Open in Browser
echo.
echo ============================================================
echo   LoanWise AI — Opening Application
echo ============================================================
echo.

REM Check if backend is running
curl -s --connect-timeout 3 http://localhost:8000/api/health > nul 2>&1
if %ERRORLEVEL%==0 (
    echo   [OK] Backend is running on http://localhost:8000
) else (
    echo   [WARNING] Backend is not running!
    echo.
    echo   Please open START_LOANWISE.bat first, wait for it to say
    echo   "Uvicorn running on http://0.0.0.0:8000", then run this again.
    echo.
    pause
    exit /b 0
)

echo.
echo   Opening LoanWise AI in your browser...
echo.

REM Try frontend server on 5502 first
netstat -an 2>nul | findstr ":5502 " > nul
if %ERRORLEVEL%==0 (
    echo   Opening http://localhost:5502/index.html
    start "" "http://localhost:5502/index.html"
    goto :done
)

REM Fall back to opening the HTML file directly (works in Chrome/Edge)
echo   Opening frontend\index.html directly...
start "" "%~dp0frontend\index.html"

:done
echo.
echo   ============================================================
echo   Login:  anantha@example.com  /  Demo@123
echo   Admin:  admin@loanwise.ai    /  Admin@123
echo   ============================================================
echo.
timeout /t 3 /nobreak > nul

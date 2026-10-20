@echo off
title LoanWise AI ??? Frontend Server
echo.
echo ============================================================
echo   LoanWise AI ??? Frontend Server
echo   (Port 5500/5501 reserved by Oracle on this machine)
echo ============================================================
echo.

REM Frontend folder is next to this .bat file
set FRONTEND=%~dp0frontend
cd /d "%FRONTEND%"

if not exist "index.html" (
    echo   [ERROR] Cannot find index.html in: %FRONTEND%
    pause
    exit /b 1
)

REM Find first free port (skip 5500 and 5501 - blocked by Oracle TNS)
set PORT=0

netstat -an 2>nul | findstr ":5502 " > nul
if %ERRORLEVEL%==1 ( set PORT=5502 & goto :start )

netstat -an 2>nul | findstr ":5503 " > nul
if %ERRORLEVEL%==1 ( set PORT=5503 & goto :start )

netstat -an 2>nul | findstr ":8080 " > nul
if %ERRORLEVEL%==1 ( set PORT=8080 & goto :start )

netstat -an 2>nul | findstr ":3000 " > nul
if %ERRORLEVEL%==1 ( set PORT=3000 & goto :start )

set PORT=9000

:start
echo   Starting on port %PORT%...
echo.
echo   ============================================================
echo   Open in your browser:
echo     http://localhost:%PORT%/index.html
echo     http://localhost:%PORT%/login.html
echo   ============================================================
echo.
echo   Make sure backend is running: http://localhost:8000
echo   (Run START_LOANWISE.bat in another window if not started)
echo.
echo   Press Ctrl+C to stop.
echo.
python -m http.server %PORT%

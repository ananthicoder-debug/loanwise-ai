@echo off
title LoanWise AI ??? Switch to Local MongoDB
echo.
echo ============================================================
echo   LoanWise AI ??? Switching to Local MongoDB
echo ============================================================
echo.

set BACKEND=%~dp0backend
copy /Y "%BACKEND%\.env.local" "%BACKEND%\.env" > nul
echo   [OK] Switched to local MongoDB
echo   URI: mongodb://localhost:27017
echo   Database: loan_ai_system
echo.
echo   Make sure local MongoDB is running (START_MONGODB.bat)
echo   then run START_LOANWISE.bat
echo.
pause

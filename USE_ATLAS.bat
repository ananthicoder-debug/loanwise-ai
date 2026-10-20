@echo off
title LoanWise AI ??? Switch to MongoDB Atlas
echo.
echo ============================================================
echo   LoanWise AI ??? Switching to MongoDB Atlas
echo   Cluster: cluster0.ckt9xiq.mongodb.net
echo ============================================================
echo.

set BACKEND=%~dp0backend
copy /Y "%BACKEND%\.env.production" "%BACKEND%\.env" > nul
echo   [OK] Switched to MongoDB Atlas configuration
echo   Database: loan_ai_system (cloud.mongodb.com)
echo.
echo   Testing connection...
cd /d "%BACKEND%"
python test_atlas.py
echo.
pause

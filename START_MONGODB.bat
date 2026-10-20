@echo off
title LoanWise AI — Start MongoDB
echo.
echo ============================================================
echo   LoanWise AI — Starting MongoDB
echo ============================================================
echo.

REM Check if already running
netstat -an | findstr ":27017 " > nul
if %ERRORLEVEL%==0 (
    echo   [OK] MongoDB is already running on port 27017.
    echo   You can now run START_LOANWISE.bat
    pause
    exit /b 0
)

REM Create data directory
if not exist "C:\data\db" (
    mkdir "C:\data\db"
    echo   Created C:\data\db
)

REM Write MongoDB config with FTDC disabled (fixes crash on MongoDB 8.3 Windows)
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

echo   Starting MongoDB (port 27017)...
start "MongoDB Server" /min "C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe" --config "C:\data\mongod.cfg"

echo   Waiting for MongoDB to initialize...
timeout /t 8 /nobreak > nul

REM Verify
netstat -an | findstr ":27017 " > nul
if %ERRORLEVEL%==0 (
    echo.
    echo   [OK] MongoDB is running on port 27017
    echo   You can now run START_LOANWISE.bat
) else (
    echo.
    echo   [WARNING] MongoDB may still be starting up.
    echo   Wait a few more seconds, or check C:\data\mongod.log for errors.
    echo   If problem persists, try running this script as Administrator.
)

echo.
pause

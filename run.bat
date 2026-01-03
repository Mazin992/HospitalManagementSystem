@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Move to script directory (CRITICAL FIX)
cd /d "%~dp0"

echo ======================================
echo  Hospital Management System Setup
echo ======================================
echo.

REM -------------------------------
REM Check Python
REM -------------------------------
echo Checking Python...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ❌ Python is NOT installed.
    echo Please install Python 3.9+ from:
    echo https://www.python.org/downloads/
    pause
    exit /b
)

FOR /F "tokens=2 delims= " %%A IN ('python --version') DO (
    SET PY_VER=%%A
)
echo ✅ Python %PY_VER% found
echo.

REM -------------------------------
REM Check Git
REM -------------------------------
echo Checking Git...
git --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ❌ Git is NOT installed.
    echo Please install Git from:
    echo https://git-scm.com/downloads
    pause
    exit /b
)
echo ✅ Git installed
echo.

REM -------------------------------
REM Check PostgreSQL
REM -------------------------------
echo Checking PostgreSQL...
psql --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ❌ PostgreSQL is NOT installed.
    echo Please install PostgreSQL from:
    echo https://www.postgresql.org/download/windows/
    pause
    exit /b
)
echo ✅ PostgreSQL installed
echo.

REM -------------------------------
REM Create Virtual Environment
REM -------------------------------
echo Creating virtual environment...
IF NOT EXIST venv (
    python -m venv venv
)
call venv\Scripts\activate
echo ✅ Virtual environment activated
echo.

REM -------------------------------
REM Upgrade pip
REM -------------------------------
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM -------------------------------
REM Install dependencies
REM -------------------------------
echo Installing dependencies...
pip install -r requirements.txt
pip install psycopg2-binary
echo ✅ Dependencies installed
echo.

REM -------------------------------
REM Environment Variables
REM -------------------------------
echo Setting environment variables...
setx FLASK_CONFIG development

echo.
echo --------------------------------------
echo IMPORTANT DATABASE SETUP REQUIRED
echo --------------------------------------
echo Setting up PostgreSQL database...
python setup_database.py
IF ERRORLEVEL 1 (
    echo ❌ Database setup failed.
    pause
    exit /b
)
echo ✅ Database setup completed
echo.
REM Load environment variables from .env file
if exist .env (
    echo Loading environment variables from .env file...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        REM Skip empty lines and comments
        if not "!line!"=="" if not "!line:~0,1!"=="#" (
            set "%%a=%%b"
        )
    )
    echo ✓ Environment variables loaded
) else (
    echo ❌ Database initialization failed.
    echo Check Failed to get .env File.
    pause
    exit /b
)
echo.
echo Database User:     %DB_USER%
echo Database Host:     %DB_HOST%
echo Database Port:     %DB_PORT%
echo Database Name:     %DB_NAME%
echo.
echo Full DATABASE_URL:
echo    postgresql://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%
echo.

REM Optional: Set DATABASE_URL environment variable
set DATABASE_URL=postgresql://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%

echo After that, press any key to continue...
pause

REM -------------------------------
REM Initialize Database
REM -------------------------------
echo Initializing database...
python init_db.py
IF ERRORLEVEL 1 (
    echo ❌ Database initialization failed.
    echo Check DATABASE_URL and PostgreSQL credentials.
    pause
    exit /b
)
echo ✅ Database initialized
echo.

REM -------------------------------
REM Run Application
REM -------------------------------
echo Starting application...
python run.py

ENDLOCAL
pause
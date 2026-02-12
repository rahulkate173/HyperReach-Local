@echo off
REM Cold Outreach Engine - Setup Script for Windows
REM Installs dependencies and sets up the project

echo.
echo ================================
echo 🚀 Cold Outreach Engine Setup
echo ================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% found
echo.

REM Check if uv is installed
echo Checking for uv package manager...
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing uv package manager...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    call refreshenv
    echo ✓ uv installed
) else (
    for /f "tokens=*" %%i in ('uv --version') do set UV_VERSION=%%i
    echo ✓ !UV_VERSION! found
)
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📁 Creating virtual environment...
    python -m venv .venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo ⚙️  Activating virtual environment...
call .venv\Scripts\activate.bat
echo.

REM Install dependencies using uv
echo 📦 Installing dependencies...
uv pip install -e .
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

REM Create necessary directories
echo 📁 Creating data directories...
if not exist "data" mkdir data
if not exist "models" mkdir models
if not exist "logs" mkdir logs
echo ✓ Directories created
echo.

REM Create cache directory
echo 🔄 Preparing model cache directory...
if not exist "models\.cache" mkdir models\.cache
echo ✓ Cache directory ready
echo.

echo ================================
echo ✅ Setup Complete!
echo ================================
echo.
echo To start the server, run:
echo.
echo   .venv\Scripts\activate.bat
echo   python -m backend.api
echo.
echo Or for development with auto-reload:
echo.
echo   uv run uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
echo.
echo Then open your browser to: http://127.0.0.1:8000
echo.
echo For chat interface: http://127.0.0.1:8000/chat
echo.
pause

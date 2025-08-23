@echo off
REM FFF Growth System v2 Installation Script for Windows
REM This script sets up the development environment

echo 🚀 Setting up FFF Growth System v2...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Error: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Install development dependencies
echo 🔧 Installing development dependencies...
pip install pytest pytest-cov black flake8 mypy

echo ✅ Installation complete!
echo.
echo To activate the environment:
echo   venv\Scripts\activate.bat
echo.
echo To run tests:
echo   python -m pytest tests/
echo.
echo To run the UI:
echo   streamlit run ui/app.py
echo.
echo To run a simulation:
echo   python simulate_fff_growth.py --preset baseline
echo.
pause

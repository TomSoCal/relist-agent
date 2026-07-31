@echo off
REM Panda Profit Launcher
REM Start the application from the current directory

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Launch the application
echo Starting Panda Profit...
python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Panda Profit failed to start
    echo.
    pause
)

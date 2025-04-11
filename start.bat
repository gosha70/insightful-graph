@echo off
REM Start script for Knowledge Graph Builder on Windows
REM This script helps users set up and run the application in one step

echo =======================================
echo Knowledge Graph Builder - Quick Start
echo =======================================

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher and try again
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.8 or higher is required
    echo Current Python version: %PYTHON_VERSION%
    pause
    exit /b 1
)

if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% LSS 8 (
        echo Error: Python 3.8 or higher is required
        echo Current Python version: %PYTHON_VERSION%
        pause
        exit /b 1
    )
)

echo Python version: %PYTHON_VERSION%

REM Check if Neo4j is running
echo.
echo Checking Neo4j status...
python -c "import sys; from neo4j import GraphDatabase; try: driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); with driver.session() as session: result = session.run('RETURN 1 AS test'); result.single(); driver.close(); sys.exit(0); except Exception as e: sys.exit(1)" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Neo4j is running
    set NEO4J_RUNNING=true
) else (
    echo Warning: Neo4j is not running or not accessible
    echo You can still use the application, but you won't be able to build or visualize graphs
    echo Please make sure Neo4j is running and accessible at bolt://localhost:7687
    echo Default credentials: username=neo4j, password=password
    set NEO4J_RUNNING=false
    
    REM Ask user if they want to continue
    set /p CONTINUE=Do you want to continue anyway? (y/n): 
    if /i not "%CONTINUE%"=="y" (
        echo Exiting. Please start Neo4j and try again.
        pause
        exit /b 1
    )
)

REM Check if dependencies are installed
echo.
echo Checking dependencies...
python -c "import sys; try: import streamlit, pandas, neo4j, networkx, matplotlib; sys.exit(0); except ImportError as e: print(f'Missing dependency: {str(e)}'); sys.exit(1)" >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo Some dependencies are missing. Running setup...
    
    REM Run setup script
    python setup.py
    
    REM Check if setup was successful
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Setup failed
        echo Please run setup.py manually and check for errors
        pause
        exit /b 1
    )
) else (
    echo All dependencies are installed
)

REM Start the application
echo.
echo Starting Knowledge Graph Builder...
python run.py

REM Exit with the status of the run script
exit /b %ERRORLEVEL%

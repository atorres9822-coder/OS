@echo off
::
:: Mini OS Simulator - Launcher Script (Windows)
# Runs the Mini OS desktop application.
::
# Usage:
#   run.bat
::
# This script:
#   1. Sets the working directory to the project root
#   2. Activates a virtual environment if one is present (.venv, venv, env, .env)
#   3. Runs main.py using python3.14 (or falls back to python)
::

setlocal enabledelayedexpansion

REM Resolve the directory containing this script
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Determine the Python interpreter to use.
REM Priority:
REM   1. Virtual environment python (if .venv, venv, env, .env exists)
REM   2. python3.14 (the project's tested interpreter)
REM   3. python3
REM   4. python

set PYTHON=

:: Check for a virtual environment
for %%V in (.venv venv env .env) do (
    if exist "%SCRIPT_DIR%\%%V\Scripts\python.exe" (
        set PYTHON=%%SCRIPT_DIR%%\%%V\Scripts\python.exe
        goto :found_python
    )
)

:find_system_python
REM Fall back to system interpreters
where python3.14 >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python3.14
    goto :found_python
)

where python3 >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python3
    goto :found_python
)

where python >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :found_python
)

echo Error: No Python interpreter found. >&2
echo Please install Python 3.8+ and try again. >&2
goto :eof

:found_python
echo Using Python: %PYTHON%
echo Project directory: %SCRIPT_DIR%
echo.

:: Run the application
"%PYTHON%" main.py %*

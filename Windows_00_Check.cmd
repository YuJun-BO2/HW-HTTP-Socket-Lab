@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
py -3 --version >nul 2>nul
if errorlevel 1 goto use_python
py -3 windows_preflight.py --port 8080
goto done
:use_python
python --version >nul 2>nul
if errorlevel 1 goto missing_python
python windows_preflight.py --port 8080
goto done
:missing_python
echo Python 3.10+ is not available. Install Python and reopen this terminal.
:done
echo.
pause

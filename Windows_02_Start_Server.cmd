@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "STUDENT_ID=%~1"
if not "%STUDENT_ID%"=="" goto id_ready
set /p STUDENT_ID=Enter your student ID (e.g. S12345678): 
:id_ready
if "%STUDENT_ID%"=="" goto invalid_id
py -3 --version >nul 2>nul
if errorlevel 1 goto use_python
py -3 starter_server.py --student-id "%STUDENT_ID%" --port 8080
goto done
:use_python
python --version >nul 2>nul
if errorlevel 1 goto missing_python
python starter_server.py --student-id "%STUDENT_ID%" --port 8080
goto done
:invalid_id
echo Missing student ID.
goto done
:missing_python
echo Python 3.10+ is not available. Install Python and reopen this terminal.
:done
echo.
pause

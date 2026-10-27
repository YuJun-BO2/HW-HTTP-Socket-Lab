@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "STUDENT_ID=%~1"
if not "%STUDENT_ID%"=="" goto id_ready
set /p STUDENT_ID=Enter your student ID (e.g. S12345678): 
:id_ready
if "%STUDENT_ID%"=="" goto invalid_id
set "STAGE=%~2"
if not "%STAGE%"=="" goto stage_ready
set /p STAGE=Enter stage (before or after): 
:stage_ready
if /i "%STAGE%"=="before" goto stage_valid
if /i "%STAGE%"=="after" goto stage_valid
echo Stage must be before or after.
goto done
:stage_valid
py -3 --version >nul 2>nul
if errorlevel 1 goto use_python
py -3 public_tests.py --student-id "%STUDENT_ID%" --port 8080 --log "public_test_%STAGE%.txt"
goto done
:use_python
python --version >nul 2>nul
if errorlevel 1 goto missing_python
python public_tests.py --student-id "%STUDENT_ID%" --port 8080 --log "public_test_%STAGE%.txt"
goto done
:invalid_id
echo Missing student ID.
goto done
:missing_python
echo Python 3.10+ is not available. Install Python and reopen this terminal.
:done
echo.
pause

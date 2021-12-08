@echo off
setlocal EnableExtensions

:start_python_files
start "1st" "spotiAFK.py"

:check_python_files
call:infinite 1st spotiAFK.py
goto:check_python_files

:infinite
tasklist /FI "WINDOWTITLE eq %1 - %2" | findstr /c:PID > nul
if %errorlevel% EQU 1 (start "%1" "%2")
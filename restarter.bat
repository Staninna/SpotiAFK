@echo off
setlocal EnableExtensions
cd /d "%~dp0"

:loop
python spotiAFK.py
if %errorlevel% EQU 0 goto :eof
echo spotiAFK crashed, restarting in 5 seconds...
timeout /t 5 /nobreak > nul
goto :loop

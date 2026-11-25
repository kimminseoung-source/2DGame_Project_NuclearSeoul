@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" "tools\run_pistol_comparison.py"
if errorlevel 1 pause

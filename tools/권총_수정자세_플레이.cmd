@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" "tools\run_shared_pistol_trial.py"
if errorlevel 1 pause

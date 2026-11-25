@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" "tools\run_redjacket_trial.py"
if errorlevel 1 pause

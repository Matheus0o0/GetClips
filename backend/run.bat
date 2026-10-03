@echo off
cd /d "%~dp0"
echo [Backend] Logs em: %~dp0..\storage\logs\app.log
echo [Backend] Iniciando...
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1 --loop asyncio
pause

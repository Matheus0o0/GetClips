@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if not exist "%ROOT%\backend\.venv\Scripts\activate.bat" (
    echo ERRO: venv nao encontrado. Execute scripts\install.ps1 primeiro.
    pause & exit /b 1
)

echo Parando processos anteriores...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%p /F >nul 2>&1

start "Ollama" ollama serve
timeout /t 2 /nobreak >nul
start "Backend" "%ROOT%\backend\run.bat"
timeout /t 3 /nobreak >nul
start "Frontend" "%ROOT%\frontend\run.bat"
timeout /t 5 /nobreak >nul
start "" "http://localhost:3000"
endlocal

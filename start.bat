@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if not exist "%ROOT%\backend\.venv\Scripts\activate.bat" (
    echo ERRO: venv nao encontrado. Execute scripts\install.ps1 primeiro.
    pause & exit /b 1
)

start "Ollama" /min ollama serve
timeout /t 2 /nobreak >nul
start "Backend" /min "%ROOT%\backend\run.bat"
timeout /t 3 /nobreak >nul
start "Frontend" /min "%ROOT%\frontend\run.bat"
timeout /t 5 /nobreak >nul
start "" "http://localhost:3000"
endlocal

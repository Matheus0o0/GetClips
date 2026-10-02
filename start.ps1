# TranscreverVideoYt — launcher
param([switch]$NoBrowser)

$root = $PSScriptRoot

$venv  = "$root\backend\.venv\Scripts\activate.bat"
$nmods = "$root\frontend\node_modules"

if (-not (Test-Path $venv)) {
    Write-Host "ERRO: venv nao encontrado. Execute scripts\install.ps1 primeiro." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}
if (-not (Test-Path $nmods)) {
    Write-Host "ERRO: node_modules nao encontrado. Execute scripts\install.ps1 primeiro." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Escreve batches temporarios para evitar problemas de quoting com espacos no path
$tmpBack  = "$env:TEMP\neo_backend.bat"
$tmpFront = "$env:TEMP\neo_frontend.bat"

@"
@echo off
title Backend - TranscreverVideoYt
cd /d "$root\backend"
call ".venv\Scripts\activate.bat"
uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
pause
"@ | Set-Content -LiteralPath $tmpBack -Encoding ascii

@"
@echo off
title Frontend - TranscreverVideoYt
cd /d "$root\frontend"
npm run dev
pause
"@ | Set-Content -LiteralPath $tmpFront -Encoding ascii

Write-Host "Iniciando backend  (http://127.0.0.1:8000) ..." -ForegroundColor Cyan
$backendProc = Start-Process cmd -ArgumentList "/k `"$tmpBack`"" -PassThru

Start-Sleep -Milliseconds 300

Write-Host "Iniciando frontend (http://localhost:3000) ..." -ForegroundColor Cyan
$frontendProc = Start-Process cmd -ArgumentList "/k `"$tmpFront`"" -PassThru

if (-not $NoBrowser) {
    Write-Host "Aguardando servicos (5s) ..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:3000"
}

"$($backendProc.Id),$($frontendProc.Id)" | Set-Content "$root\.pids" -Encoding utf8

Write-Host ""
Write-Host "App rodando!" -ForegroundColor Green
Write-Host "  UI:  http://localhost:3000" -ForegroundColor White
Write-Host "  API: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Para parar: scripts\stop.ps1" -ForegroundColor Gray

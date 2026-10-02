# LocalTranscriber - Windows installer
$ErrorActionPreference = "Stop"

Write-Host "==> Verificando pré-requisitos..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: Python não encontrado. Instale Python 3.12+." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: Node.js não encontrado. Instale Node 20+." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "AVISO: FFmpeg não encontrado no PATH." -ForegroundColor Yellow
    Write-Host "Instale com: winget install Gyan.FFmpeg" -ForegroundColor Yellow
}

$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Criando venv do backend..." -ForegroundColor Cyan
python -m venv "$root/backend/.venv"

Write-Host "==> Instalando dependências Python..." -ForegroundColor Cyan
& "$root/backend/.venv/Scripts/pip.exe" install --upgrade pip
& "$root/backend/.venv/Scripts/pip.exe" install -e "$root/backend"

Write-Host "==> Instalando dependências Node..." -ForegroundColor Cyan
Push-Location "$root/frontend"
npm install
Pop-Location

Write-Host "==> Criando diretórios de storage..." -ForegroundColor Cyan
$dirs = @("downloads","audio","outputs/subtitles","outputs/transcripts","cache","models","logs","temp")
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path "$root/storage/$d" | Out-Null
}

if (-not (Test-Path "$root/backend/.env")) {
    Copy-Item "$root/backend/.env.example" "$root/backend/.env"
    Write-Host "==> Criado backend/.env a partir de .env.example" -ForegroundColor Green
}

Write-Host ""
Write-Host "Instalação concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar em desenvolvimento:" -ForegroundColor Cyan
Write-Host "  Terminal 1: cd backend; .venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"
Write-Host "  Terminal 2: cd frontend; npm run dev"
Write-Host ""
Write-Host "Depois acesse: http://localhost:3000" -ForegroundColor Cyan

#!/usr/bin/env bash
# LocalTranscriber - Unix installer
set -euo pipefail

echo "==> Verificando pré-requisitos..."

command -v python3 >/dev/null 2>&1 || { echo "ERRO: Python 3.12+ não encontrado."; exit 1; }
command -v node    >/dev/null 2>&1 || { echo "ERRO: Node 20+ não encontrado."; exit 1; }
command -v ffmpeg  >/dev/null 2>&1 || echo "AVISO: FFmpeg não encontrado. Instale antes de rodar."

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Criando venv do backend..."
python3 -m venv "$ROOT/backend/.venv"

echo "==> Instalando dependências Python..."
"$ROOT/backend/.venv/bin/pip" install --upgrade pip
"$ROOT/backend/.venv/bin/pip" install -e "$ROOT/backend"

echo "==> Instalando dependências Node..."
(cd "$ROOT/frontend" && npm install)

echo "==> Criando diretórios de storage..."
for d in downloads audio outputs/subtitles outputs/transcripts cache models logs temp; do
    mkdir -p "$ROOT/storage/$d"
done

if [ ! -f "$ROOT/backend/.env" ]; then
    cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
    echo "==> Criado backend/.env"
fi

echo
echo "Instalação concluída!"
echo
echo "Para iniciar em desenvolvimento:"
echo "  Terminal 1: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "  Terminal 2: cd frontend && npm run dev"
echo
echo "Depois acesse: http://localhost:3000"

# GetClips

Transcreve vídeos localmente e gera cortes verticais automáticos (Reels / Shorts) com reenquadramento dinâmico por rastreamento de rosto.

> **Privacidade:** vídeo, áudio, detecção de rosto e renderização são **100% locais**.
> Usando Ollama como provedor de IA, nenhum dado sai da máquina.
> Usando OpenAI ou Anthropic, apenas o **texto** da transcrição é enviado — nunca o vídeo.

---

## Funcionalidades

- **Transcrição local** via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CPU ou GPU CUDA)
- **Sugestão de cortes** via LLM — Ollama (local) ou OpenAI / Anthropic (só texto sai)
- **Reenquadramento 9:16** com KalmanSmoother, dead zone e offset de corpo
- **Detecção de rosto** com MediaPipe + scoring temporal (consistência entre frames)
- **Renderização de clipes** com FFmpeg
- **Download de vídeos** via yt-dlp (YouTube, etc.)
- Interface web React com progresso em tempo real via WebSocket

---

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | React 18 + Vite + TypeScript + Tailwind + shadcn/ui |
| Backend | FastAPI + Python 3.12 + SQLite (aiosqlite) |
| Transcrição | faster-whisper (Whisper Large-v3 / Distil-Large-v3) |
| Vídeo | yt-dlp + FFmpeg + OpenCV + MediaPipe |
| IA (cortes) | Ollama local · OpenAI · Anthropic (configurável) |

---

## Pré-requisitos

- **Python** 3.12+
- **Node.js** 20+
- **FFmpeg** no PATH — `ffmpeg -version` deve funcionar
  - Windows: `winget install Gyan.FFmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- **Ollama** (recomendado, totalmente local) — [ollama.com](https://ollama.com)
  - Após instalar: `ollama pull llama3.2`
- **CUDA 12.x** *(opcional)* — para GPU NVIDIA na transcrição
- **Chave de API** *(opcional)* — só se não usar Ollama

---

## Instalação

### Windows (PowerShell)

```powershell
.\scripts\install.ps1
```

### macOS / Linux

```bash
./scripts/install.sh
```

O script cria o virtualenv, instala dependências Python e Node, e cria os diretórios de `storage/`.

---

## Execução

### Windows — um clique

```
start.bat
```

Abre Ollama, backend e frontend em segundo plano e lança o navegador em `http://localhost:3000`.

### Manual

```bash
# Terminal 1 — backend
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

---

## Configuração

Copie `backend/.env.example` para `backend/.env` e ajuste:

```env
# Provedor de IA para seleção de cortes
# Opções: ollama | openai | anthropic | none
HIGHLIGHT_PROVIDER=ollama

# Ollama (local, sem custo)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenAI (opcional)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Anthropic (opcional)
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

# Transcrição
DEFAULT_MODEL=distil-large-v3
DEFAULT_LANGUAGE=pt
DEVICE=auto          # auto | cuda | cpu
```

---

## Modelos de transcrição

| Modelo | Tamanho | Quando usar |
|---|---|---|
| `tiny` | ~40 MB | Testes rápidos |
| `base` | ~75 MB | CPU modesta |
| `small` | ~250 MB | Balanço CPU |
| `medium` | ~770 MB | Boa qualidade |
| `large-v3` | ~1.5 GB | Máxima qualidade (GPU) |
| `distil-large-v3` | ~750 MB | Quase-large, 6× mais rápido — **padrão** |

Modelos são baixados automaticamente na primeira execução para `storage/models/`.

---

## Como funciona o reframe

1. A LLM analisa a transcrição e sugere intervalos `[inicio, fim]` com score e hook
2. Para cada clipe, o pipeline extrai o trecho do vídeo original
3. MediaPipe detecta rostos frame a frame com stride configurável
4. KalmanSmoother suaviza a trajetória do centro de crop
5. Dead zone evita micromovimentos; body offset enquadra ombros junto ao rosto
6. FFmpeg renderiza o clipe 9:16 final

---

## Estrutura

```
├── backend/
│   ├── app/
│   │   ├── api/          # Rotas FastAPI
│   │   ├── application/  # Use cases + orquestrador de jobs
│   │   ├── core/         # Entidades, interfaces, exceções
│   │   ├── services/     # Whisper, FFmpeg, Ollama, reframe
│   │   └── infrastructure/ # SQLite, container DI
│   └── run.bat
├── frontend/
│   └── src/
│       ├── features/     # clips/, jobs/
│       ├── pages/
│       └── shared/
├── scripts/              # install.ps1 / install.sh
├── storage/              # gerado em runtime (gitignored)
└── start.bat
```

---

## Licença

MIT

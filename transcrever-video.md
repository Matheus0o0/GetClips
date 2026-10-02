# LocalTranscriber → Gerador de Cortes

Aplicação desktop-first que transcreve vídeos **localmente** e usa a
transcrição para gerar **cortes verticais automáticos** (estilo Reels/Shorts),
com reenquadramento dinâmico por rastreamento de rosto/pessoa.

> **Escopo de privacidade (importante):** o vídeo e o áudio nunca saem da
> máquina. Transcrição, detecção de rosto e corte/render são 100% locais.
> **Apenas o texto da transcrição** é enviado a uma API externa (OpenAI ou
> Anthropic) para identificar os trechos relevantes. Isso precisa ficar
> explícito na UI (ex.: aviso na tela de configuração), já que muda a
> promessa original do produto de "100% offline".

- **Frontend:** React + Vite + TypeScript + TailwindCSS + shadcn/ui
- **Backend:** FastAPI + Python 3.12 + SQLite + faster-whisper
- **Vídeo:** yt-dlp + FFmpeg + OpenCV + MediaPipe
- **IA (transcrição):** Whisper Large-v3 / Distil-Large-v3, local (GPU CUDA ou CPU)
- **IA (seleção de cortes):** LLM externa (OpenAI ou Anthropic, configurável) — só texto

---

## Pré-requisitos

- **Python** 3.12+
- **Node.js** 20+
- **FFmpeg** disponível no PATH (`ffmpeg -version` deve funcionar)
- **CUDA 12.x** (opcional — para aceleração por GPU NVIDIA na transcrição)
- **Chave de API** (OpenAI ou Anthropic) — necessária apenas para a etapa de
  seleção de trechos. Sem chave configurada, essa etapa fica indisponível
  (não há fallback automático nesta versão — ver §Roadmap).

Instalação do FFmpeg no Windows: `winget install Gyan.FFmpeg`
No macOS: `brew install ffmpeg`
No Linux (Debian/Ubuntu): `sudo apt install ffmpeg`

---

## Instalação

### Windows (PowerShell)

```powershell
./scripts/install.ps1
```

### macOS / Linux

```bash
./scripts/install.sh
```

O script:
1. Cria um ambiente virtual em `backend/.venv`
2. Instala as dependências Python (inclui `mediapipe`, `opencv-python` e o SDK da LLM escolhida)
3. Instala as dependências do frontend
4. Cria os diretórios de `storage/`

---

## Execução

### Modo desenvolvimento (dois terminais)

Terminal 1 — Backend:

```bash
cd backend
.venv/Scripts/activate    # Windows
# source .venv/bin/activate    # Linux/Mac
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — Frontend:

```bash
cd frontend
npm run dev
```

Acesse: **http://localhost:3000**

---

## Pipeline

```
vídeo
  │
  ▼
1. Transcrição (Whisper local)
   → texto + timestamps por segmento
  │
  ▼
2. Seleção de trechos (LLM externa — OpenAI/Anthropic, só texto)
   → lista de candidatos: início, fim, hook, score, motivo
  │
  ▼
3. Corte + reenquadramento vertical (100% local)
   → detecção de rosto/pessoa (MediaPipe) + tracking suavizado
   → crop dinâmico (OpenCV) + remux de áudio (FFmpeg)
  │
  ▼
4. Export 1080x1920 (clips prontos)
```

### Etapa 2 — Seleção de trechos (LLM externa)

Novo serviço `services/highlight_llm.py`.

- **Input:** transcrição com timestamps (segments do Whisper) + parâmetros
  do usuário (nº de cortes desejado, duração alvo, ex. 30–60s).
- **Prompt** pede um JSON estruturado com os candidatos:

  ```json
  [
    {
      "inicio": 132.4,
      "fim": 178.9,
      "hook": "frase de abertura do corte",
      "score": 0.87,
      "motivo": "pico emocional / resposta direta a uma pergunta"
    }
  ]
  ```

- **Validação obrigatória** da resposta antes de aceitar: schema (campos e
  tipos corretos), `inicio`/`fim` dentro da duração real do vídeo, `fim >
  inicio`, duração dentro da faixa pedida. LLM pode alucinar timestamp — nunca
  confiar sem checar contra os segments reais do Whisper.
- **Provedor configurável** via `.env`: `HIGHLIGHT_PROVIDER=openai|anthropic`.
  Chave de API fica **só no backend** (`.env`), nunca chega ao frontend.
- Sem chave configurada → a aba de cortes fica desabilitada com uma mensagem
  explicando por quê (evita erro confuso na hora do request).

### Etapa 3 — Corte + reenquadramento (tracking dinâmico, 100% local)

A parte pesada, e a que faz o corte parecer "editado por gente":

- **Detecção:** MediaPipe Face Detection como primário (rápido em CPU). Se
  não detectar rosto num trecho (plano aberto, tela, gráfico), cai para
  MediaPipe Pose/Object detection; se nada for detectado, cai para **crop
  central fixo** nesse trecho específico — sem alvo não há o que seguir.
- **Amostragem:** detecção roda a cada N frames (ex. a cada 5), não em 100%
  — reduz custo. Posições intermediárias são interpoladas.
- **Suavização:** média móvel (ou filtro tipo Kalman) sobre o centro
  detectado ao longo do tempo. Sem isso o crop "treme" a cada micro-movimento
  de cabeça — é a diferença entre parecer profissional ou amador.
- **Render:** loop em OpenCV (lê frame → aplica crop na posição suavizada →
  escreve frame do vídeo vertical) e depois remuxa o áudio original via
  FFmpeg. Mais fácil de depurar/ajustar do que tentar crop dinâmico só com
  filtros nativos do FFmpeg (`sendcmd`/`zmq`); otimização de performance fica
  para depois se necessário.
- **Saída:** 1080×1920 (9:16), pronta para Reels/Shorts/TikTok.

---

## Estrutura do projeto

```text
local-transcriber/
├── backend/                 # FastAPI + Python
│   └── app/
│       ├── api/             # Presentation (routers, websocket)
│       ├── core/            # Domain (entities, interfaces)
│       ├── application/     # Use cases, orchestrator, pipeline
│       ├── services/
│       │   ├── whisper.py          # transcrição local
│       │   ├── ytdlp.py            # download de vídeo
│       │   ├── ffmpeg.py           # remux/áudio/export
│       │   ├── highlight_llm.py    # seleção de trechos (API externa, só texto)
│       │   └── reframe/            # detecção, tracking, crop dinâmico
│       │       ├── detector.py     # MediaPipe (face/pose)
│       │       ├── smoothing.py    # média móvel / Kalman
│       │       └── render.py       # loop OpenCV + remux FFmpeg
│       └── infrastructure/  # DB, storage, event bus, logging
├── frontend/                # React + Vite
│   └── src/
│       ├── app/             # Router, providers, layout
│       ├── features/
│       │   ├── jobs/
│       │   ├── history/
│       │   ├── settings/           # chave de API, provedor, parâmetros
│       │   └── clips/              # nova aba: candidatos, preview, render
│       ├── shared/          # ui, lib, hooks, types
│       └── pages/
├── storage/                 # Dados do usuário (fora do código)
│   ├── downloads/
│   ├── audio/
│   ├── outputs/
│   ├── clips/               # cortes verticais renderizados
│   ├── models/              # Modelos Whisper baixados
│   └── logs/
└── scripts/                 # Instalação e utilitários
```

---

## Configuração

Copie `backend/.env.example` para `backend/.env` e ajuste:

```
STORAGE_ROOT=../storage
DEFAULT_MODEL=distil-large-v3
DEFAULT_LANGUAGE=pt
DEVICE=auto              # auto | cuda | cpu
MAX_CONCURRENT_JOBS=1

# Seleção de cortes (LLM externa — apenas texto trafega)
HIGHLIGHT_PROVIDER=openai        # openai | anthropic
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
HIGHLIGHT_MAX_CLIPS=5
HIGHLIGHT_CLIP_DURATION_MIN=30
HIGHLIGHT_CLIP_DURATION_MAX=60

# Reenquadramento vertical
REFRAME_DETECTION_STRIDE=5       # roda detecção a cada N frames
REFRAME_SMOOTHING=moving_average # moving_average | kalman
REFRAME_OUTPUT_RESOLUTION=1080x1920
```

---

## Modelo de dados (novas tabelas)

```
clips
  id            uuid
  job_id        fk -> jobs
  inicio        float (segundos)
  fim           float (segundos)
  hook_text     text
  score         float
  motivo        text
  crop_mode     enum (dynamic, static_fallback)
  status        enum (pendente, renderizando, pronto, erro)
  output_path   text
  created_at    timestamptz
```

---

## API (novos endpoints)

| Rota | Função |
|---|---|
| `POST /videos/{id}/highlights` | Chama a LLM externa, retorna candidatos a corte (valida contra a duração real) |
| `POST /clips/{id}/render` | Dispara detecção + tracking + crop + export do corte vertical |
| `GET /clips/{id}` | Status / caminho de download do corte |
| WebSocket existente | Reaproveitado para progresso de render (frame a frame) |

---

## Frontend — o que muda

- **Nova aba "Cortes"**: lista os candidatos retornados pela LLM (hook,
  score, motivo), usuário escolhe quais renderizar, com preview do resultado
  final.
- **Configurações**: campo para chave de API, seletor de provedor
  (OpenAI/Anthropic), nº de cortes desejado, duração alvo — com aviso claro
  de que **só o texto da transcrição** é enviado externamente.

---

## Modelos de transcrição suportados

| Modelo | Tamanho | Uso recomendado |
|---|---|---|
| `tiny` | ~40 MB | Testes rápidos |
| `base` | ~75 MB | CPU modesta |
| `small` | ~250 MB | Balanço |
| `medium` | ~770 MB | Boa qualidade |
| `large-v3` | ~1.5 GB | Máxima qualidade (GPU recomendada) |
| `distil-large-v3` | ~750 MB | Qualidade quase-large, 6x mais rápido |

Modelos são baixados automaticamente na primeira execução para `storage/models/`.

---

## Privacidade

- Bind padrão em `127.0.0.1` — apenas conexões locais.
- Sem telemetria.
- Vídeo, áudio, detecção de rosto e renderização: **nunca saem da máquina**.
- **Exceção explícita:** o texto da transcrição (sem vídeo/áudio) é enviado
  à API da LLM escolhida (OpenAI/Anthropic) para identificar trechos
  relevantes. Isso deve ser comunicado com clareza na UI.
- yt-dlp acessa apenas o site de origem do vídeo que você cola.
- Modelos de transcrição podem ser pré-baixados manualmente; a etapa de
  seleção de cortes, por depender de API externa, **não** funciona 100%
  offline.

---

## Roadmap / próximos passos sugeridos

1. **MVP do corte:** `highlight_llm.py` (1 provedor só, ex. OpenAI) +
   pipeline de reframe com MediaPipe + crop central como fallback simples.
2. **Suavização e qualidade:** ajustar o filtro de smoothing (comparar média
   móvel vs. Kalman na prática) e o stride de detecção pra achar o equilíbrio
   velocidade/qualidade.
3. **Fallback offline para seleção de trechos:** heurística local
   (palavras-chave, picos de energia de fala, pausas) para quando não houver
   chave de API configurada — evita que a feature de cortes dependa 100% de
   serviço externo.
4. **Múltiplas pessoas em quadro:** hoje o tracking assume 1 alvo principal;
   avaliar comportamento com 2+ pessoas falando (ex. entrevista) — pode
   exigir lógica de "quem está falando agora" (active speaker) usando o
   áudio + timestamps da transcrição.
5. **Legendas queimadas no corte** (opcional, natural pra Reels/Shorts) —
   reaproveita os timestamps que o Whisper já gera.

---

## Licença

MIT.

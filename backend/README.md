# Backend — LocalTranscriber

FastAPI + SQLite + faster-whisper.

## Como funciona (Clean Architecture)

```
app/
├── api/            # Presentation — FastAPI routers, DTOs, WebSocket
├── core/           # Domain — entidades, VOs, interfaces (Protocols)
├── application/    # Use cases, Pipeline, Steps, Job Queue, WorkerPool
├── services/       # Infrastructure adapters — faster-whisper, yt-dlp, ffmpeg
└── infrastructure/ # DB, storage, event bus, logging, DI container
```

**Regra de dependência:** `core/` não importa de nenhuma outra camada.

## Rodando manualmente (sem os scripts)

```bash
python -m venv .venv
.venv/Scripts/activate         # Windows
# source .venv/bin/activate    # Linux/Mac
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Health check: <http://127.0.0.1:8000/health>
OpenAPI docs: <http://127.0.0.1:8000/docs>

## API

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/jobs` | Cria job a partir de URL |
| GET  | `/api/v1/jobs` | Lista jobs |
| GET  | `/api/v1/jobs/{id}` | Detalhes de um job (com media_files) |
| DELETE | `/api/v1/jobs/{id}` | Cancela job |
| POST | `/api/v1/upload` | Upload de arquivo local |
| GET  | `/api/v1/download/{id}/{fmt}` | Baixa saída (srt, vtt, txt, md) |
| GET  | `/api/v1/history` | Alias com filtros |
| GET  | `/api/v1/settings` | Configuração atual |
| GET  | `/api/v1/models` | Modelos disponíveis (baixados ou não) |
| WS   | `/ws/jobs/{id}` | Progresso em tempo real |
| WS   | `/ws/jobs` | Feed global de eventos |

## Adicionando um novo Step ao Pipeline

1. Crie a classe em `app/application/orchestrator/steps/meu_step.py` implementando `IPipelineStep`.
2. Injete-a no `Container` em `app/infrastructure/container.py`, na lista `steps=[...]`.

Nenhuma outra camada precisa mudar.

## Adicionando um novo Downloader

1. Crie o adapter em `app/services/downloader/meu_adapter.py` implementando `IDownloader`.
2. Adicione à lista `downloaders=[...]` no `Container`.

O `DownloadStep` itera na lista e usa o primeiro que responde `True` a `can_handle(url)`.

## GPU vs CPU

`app/services/transcriber/device_detector.py` auto-detecta CUDA na inicialização:

- `DEVICE=auto` (padrão): CUDA se disponível, senão CPU
- `DEVICE=cuda`: força CUDA (falha para CPU se indisponível)
- `DEVICE=cpu`: força CPU

Verifique com: `python scripts/check_gpu.py`

## Modelos

Baixados automaticamente na primeira transcrição para `storage/models/`.
Para pré-baixar:

```bash
python scripts/download_models.py distil-large-v3
```

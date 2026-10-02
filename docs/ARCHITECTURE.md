# Arquitetura

## Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                  │
│              proxy → http://127.0.0.1:8000                  │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP + WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│              PRESENTATION LAYER (app/api)                   │
│    Routers • DTOs • WS Manager • Middleware • Exceptions    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│      APPLICATION LAYER (app/application)                    │
│  Orchestrator • Pipeline • Steps • Queue • WorkerPool       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  DOMAIN LAYER (app/core)                    │
│  Entities • Value Objects • Interfaces (Protocols) • Events │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         INFRASTRUCTURE (app/services + app/infrastructure)  │
│  faster-whisper • yt-dlp • FFmpeg • SQLite • FileSystem     │
└─────────────────────────────────────────────────────────────┘
```

## Fluxo end-to-end

```
1. User cola URL             → POST /api/v1/jobs
2. CreateJobUseCase          → Repo.save() • Queue.enqueue()
3. Retorna 202 + job_id      → Frontend abre WS /ws/jobs/{id}
4. Worker consome fila       → Orchestrator.run(job_id)
5. Pipeline.execute(ctx):
   ├─ DownloadStep           → yt-dlp / LocalFile → downloads/{job_id}/*
   ├─ ExtractAudioStep       → FFmpeg → audio/{job_id}/*.wav
   ├─ TranscribeStep         → faster-whisper → Transcription
   ├─ SubtitleStep           → gera SRT/VTT/TXT/MD → outputs/subtitles/{job_id}/
   └─ FinalizeStep           → persiste MediaFiles + Transcription
6. Cada step chama Reporter  → EventBus.publish()
7. WebSocketBridge escuta    → envia payload para clientes conectados
```

## Event Bus

Todas as atualizações fluem por eventos:

```
JobCreated → JobStageChanged → JobProgress → ... → JobCompleted
                                              ↘   → JobFailed
                                              ↘   → JobCancelled
```

Subscribers atuais:
- `WebSocketManager` — broadcast para clientes
- `JobRepository` (via `ProgressReporter`) — persiste estado throttled

## Extensibilidade

**Novo formato de saída:** adicionar em `services/subtitle/generator.py`.

**Novo downloader:** implementar `IDownloader` e registrar no `Container`.

**Novo Step (ex: diarização, tradução):** implementar `IPipelineStep` e inserir na lista de steps do `Container`.

**Novo transcritor (ex: whisper.cpp):** implementar `ITranscriber` e trocar no `Container`.

Todas essas mudanças são localizadas — nenhuma outra camada muda.

## Modelo de dados

```
jobs (1) ─── (N) media_files
jobs (1) ─── (0..1) transcriptions ─── (N) segments
```

Vídeos e áudios ficam em `storage/`; o banco guarda apenas metadados e caminhos.

## Concorrência

- `WorkerPool` inicia N asyncio tasks (default 1) consumindo a `JobQueue`
- Cada worker executa o pipeline sequencialmente por job
- Steps CPU-bound (FFmpeg, faster-whisper) rodam em thread executor
- `ProgressReporter` throttling: persiste no banco a cada 0.5s

## Ports & Adapters

Interfaces em `core/interfaces/`:

- `IDownloader` — `LocalFileDownloader`, `YtDlpDownloader`
- `ITranscriber` — `FasterWhisperTranscriber`
- `IAudioProcessor` — `FFmpegAudioProcessor`
- `ISubtitleGenerator` — `SubtitleGenerator`
- `IJobRepository` — `SQLAlchemyJobRepository`
- `IEventBus` — `InMemoryEventBus`

O `Container` faz o wiring completo em `app/infrastructure/container.py`.

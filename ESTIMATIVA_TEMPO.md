# Estimativa de Tempo de Geração

> Hardware: **RTX 2060 (6GB)** + **Ryzen 5 5600G**

## Pipeline por etapa

| Etapa | % do total | Depende de |
|-------|-----------|------------|
| Download | variável | internet (~1-5 min/GB) |
| Extração de áudio (FFmpeg) | < 5% | sempre rápido (< 30s) |
| **Transcrição (Whisper)** | **~70-85%** | modelo + hardware |
| Geração de legendas | < 5% | tamanho da transcrição |
| Finalização | < 5% | disco |

---

## RTX 2060 — CUDA (situação normal)

`device=auto` detecta a GPU. distil-large-v3 e large-v3 cabem nos 6GB de VRAM com float16.

| Vídeo | distil-large-v3 ⭐ | large-v3 | medium |
|-------|------------------|----------|--------|
| 5 min | ~5-10s | ~10-20s | ~4-8s |
| 10 min | ~10-20s | ~20-40s | ~8-15s |
| 30 min | ~30-60s | ~60-120s | ~25-45s |
| 60 min | ~60-120s | ~120-240s | ~50-90s |

⭐ Recomendado para seu hardware — melhor custo-benefício velocidade/qualidade.

## Ryzen 5 5600G — CPU fallback

Só se CUDA não estiver instalado ou `device=cpu` no `.env`.

| Vídeo | distil-large-v3 | large-v3 | medium |
|-------|----------------|----------|--------|
| 5 min | ~1.5-2.5 min | ~4-7 min | ~1-2 min |
| 10 min | ~3-5 min | ~8-14 min | ~2-4 min |
| 30 min | ~9-15 min | ~25-40 min | ~6-12 min |
| 60 min | ~18-30 min | ~50-80 min | ~12-25 min |

---

## Por que está lento / falhando?

Veja os logs do pipeline após a próxima execução — cada etapa agora registra o tempo:

```
[INFO] Iniciando step DownloadStep
[INFO] Step DownloadStep concluído em 12.3s
[INFO] Iniciando step TranscribeStep
[INFO] Step TranscribeStep concluído em 87.4s   ← gargalo aqui
```

**Log em tempo real:** `storage/logs/app.log`

**Erros catalogados via API:**
```
GET http://localhost:8000/api/v1/jobs?status=FAILED
```
Retorna todos os jobs com falha + `error_message` de cada um.

---

## Causas comuns de falha

| Erro | Causa provável |
|------|---------------|
| `NotImplementedError` no ExtractAudio | Bug asyncio Windows com subprocess (ver issue #asyncio-subprocess) |
| `JSONDecodeError` no highlight | Ollama retornou JSON malformado |
| `TranscriptionError` | Arquivo de áudio não encontrado ou corrompido |
| Job trava sem progredir | Modelo Whisper ainda carregando (primeira vez: download do modelo) |

### Primeira execução

Na primeira vez o modelo é baixado automaticamente:
- `distil-large-v3`: ~1.5 GB
- `large-v3`: ~3 GB
- Fica em `storage/models/` — próximas execuções não baixam de novo

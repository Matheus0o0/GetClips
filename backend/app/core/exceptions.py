"""Exceções do domínio."""
from __future__ import annotations


class DomainError(Exception):
    """Erro base do domínio."""


class JobNotFoundError(DomainError):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job não encontrado: {job_id}")
        self.job_id = job_id


class JobCancelledError(DomainError):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job cancelado: {job_id}")
        self.job_id = job_id


class InvalidJobStateError(DomainError):
    """Transição de estado inválida."""


class UnsupportedSourceError(DomainError):
    """URL ou arquivo não suportado por nenhum downloader."""


class TranscriptionError(DomainError):
    """Falha durante a transcrição."""


class AudioProcessingError(DomainError):
    """Falha em pré-processamento de áudio."""


class ModelNotAvailableError(DomainError):
    """Modelo Whisper não disponível/download falhou."""


class ClipNotFoundError(DomainError):
    def __init__(self, clip_id: str) -> None:
        super().__init__(f"Clip não encontrado: {clip_id}")
        self.clip_id = clip_id


class HighlightSelectionError(DomainError):
    """Falha na seleção de trechos pela LLM (resposta inválida ou erro do provedor)."""


class LLMNotConfiguredError(DomainError):
    """Provedor de LLM não configurado (chave de API ausente)."""


class ReframeError(DomainError):
    """Falha no reenquadramento vertical (detecção, crop ou render)."""


class SourceVideoUnavailableError(DomainError):
    """Vídeo original necessário para gerar o corte não está mais disponível."""


class TemplateNotFoundError(DomainError):
    def __init__(self, template_id: str) -> None:
        super().__init__(f"Template não encontrado: {template_id}")
        self.template_id = template_id

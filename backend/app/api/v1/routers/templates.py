"""Endpoints de Templates de Edição."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.dependencies import get_template_repository
from app.api.v1.schemas.common import MessageResponse
from app.editing.templates.model import EditingTemplateConfig
from app.infrastructure.database.repositories.template_repository import (
    SQLAlchemyTemplateRepository,
)

router = APIRouter(tags=["templates"])


# ── DTOs ──────────────────────────────────────────────────────────────────────

class TemplateDTO(BaseModel):
    id: str
    name: str
    is_default: bool
    config: EditingTemplateConfig

    model_config = {"from_attributes": True}

    @classmethod
    def from_row(cls, row) -> "TemplateDTO":
        return cls(
            id=row.id,
            name=row.name,
            is_default=row.is_default,
            config=SQLAlchemyTemplateRepository.config_from_row(row),
        )


class CreateTemplateRequest(BaseModel):
    name: str
    config: EditingTemplateConfig = EditingTemplateConfig()


class UpdateTemplateRequest(BaseModel):
    name: str | None = None
    config: EditingTemplateConfig | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[TemplateDTO])
async def list_templates(
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repository),
) -> list[TemplateDTO]:
    rows = await repo.list_all()
    return [TemplateDTO.from_row(r) for r in rows]


@router.post("/templates", response_model=TemplateDTO, status_code=201)
async def create_template(
    body: CreateTemplateRequest,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repository),
) -> TemplateDTO:
    row = await repo.create(body.name, body.config)
    return TemplateDTO.from_row(row)


@router.get("/templates/default", response_model=TemplateDTO | None)
async def get_default_template(
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repository),
) -> TemplateDTO | None:
    row = await repo.get_default()
    return TemplateDTO.from_row(row) if row else None


@router.get("/templates/{template_id}", response_model=TemplateDTO)
async def get_template(
    template_id: str,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repository),
) -> TemplateDTO:
    row = await repo.get(template_id)
    return TemplateDTO.from_row(row)


@router.patch("/templates/{template_id}", response_model=TemplateDTO)
async def update_template(
    template_id: str,
    body: UpdateTemplateRequest,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repository),
) -> TemplateDTO:
    row = await repo.update(template_id, body.name, body.config)
    return TemplateDTO.from_row(row)


@router.delete("/templates/{template_id}", response_model=MessageResponse)
async def delete_template(
    template_id: str,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repository),
) -> MessageResponse:
    await repo.delete(template_id)
    return MessageResponse(message="Template removido")


@router.post("/templates/{template_id}/set-default", response_model=TemplateDTO)
async def set_default_template(
    template_id: str,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repository),
) -> TemplateDTO:
    row = await repo.set_default(template_id)
    return TemplateDTO.from_row(row)

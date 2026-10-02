"""Rotas WebSocket."""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.infrastructure.container import get_container

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/jobs/{job_id}")
async def ws_job_channel(websocket: WebSocket, job_id: str) -> None:
    manager = get_container().websocket_manager
    if manager is None:
        await websocket.close(code=1011)
        return

    await manager.connect_job(job_id, websocket)
    try:
        while True:
            # Cliente pode enviar ping/pong ou comandos futuros
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, job_id=job_id)


@router.websocket("/ws/jobs")
async def ws_global_channel(websocket: WebSocket) -> None:
    manager = get_container().websocket_manager
    if manager is None:
        await websocket.close(code=1011)
        return

    await manager.connect_global(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)

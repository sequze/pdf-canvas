"""
====== API ======
GET /tasks/ - получить сохранённые задачи пользователя

GET /tasks/<task_id> - получить задачу

POST /tasks/<task_id> - создать задачу

GET /styles/ - получить доступные стили
"""

from uuid import UUID
from uuid_extensions import uuid7, uuid7str
from fastapi import APIRouter

from src.core.config import settings

router = APIRouter()


@router.get("/")
async def get_tasks():
    return []


@router.get("/{task_id}")
async def get_task(task_id: UUID):
    return


@router.post("/")
async def create_task():
    return


@router.get("/styles")
async def get_styles():
    return settings.style.styles

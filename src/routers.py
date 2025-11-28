from fastapi import APIRouter

from src.core.config import settings
from src.tasks import router as tasks_router

router = APIRouter(prefix=settings.api.prefix)

router.include_router(tasks_router, prefix=settings.api.tasks)

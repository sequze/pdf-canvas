from fastapi import APIRouter

from src.core.config import settings
from src.tasks import router as tasks_router
from src.auth import router as auth_router

router = APIRouter(prefix=settings.api.prefix)

router.include_router(auth_router)
router.include_router(tasks_router, prefix=settings.api.tasks)

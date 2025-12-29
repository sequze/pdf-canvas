from uuid import UUID
from fastapi import APIRouter, Depends, status
from shared import TaskSchema
from src.auth.schemas import UserDTO
from src.core.config import settings
from src.core.dependencies import get_current_active_user, get_task_service
from src.tasks.schemas import CreateTaskRequest, StylesResponse
from src.tasks.service import TasksService

router = APIRouter()


@router.get("/", response_model=list[TaskSchema])
async def get_tasks(
    user: UserDTO = Depends(get_current_active_user),
    task_service: TasksService = Depends(get_task_service),
) -> list[TaskSchema]:
    """Get all user`s saved tasks"""
    return await task_service.get_user_tasks(user_id=user.id)


@router.get("/styles", response_model=StylesResponse)
async def get_styles() -> StylesResponse:
    """Get list of available styles"""
    return StylesResponse(styles=settings.style.styles)


@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(
    task_id: UUID,
    user: UserDTO = Depends(get_current_active_user),
    task_service: TasksService = Depends(get_task_service),
) -> TaskSchema:
    """Get task by ID"""
    return await task_service.get_task(task_id, user.id, user.is_superuser)


@router.post("/", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: CreateTaskRequest,
    user: UserDTO = Depends(get_current_active_user),
    task_service: TasksService = Depends(get_task_service),
) -> TaskSchema:
    """Create new task"""
    return await task_service.create_task(task.data, user.id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user: UserDTO = Depends(get_current_active_user),
    task_service: TasksService = Depends(get_task_service),
) -> None:
    """Delete task"""
    await task_service.delete_task(task_id, user.id, user.is_superuser)

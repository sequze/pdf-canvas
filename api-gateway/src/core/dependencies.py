from datetime import datetime, UTC
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared import UnitOfWork, TasksRedisClient, JobsRedisClient
from src.auth.schemas import UserDTO
from src.auth.utils import decode_jwt
from src.auth.service import AuthService
from src.auth.repository import AuthRepository
from src.auth.user_repository import UserRepository
from src.core.config import settings
from src.core.db import db_helper
from src.core.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    ForbiddenError,
    NoAccessError,
)
from src.core.redis import redis_client
from src.tasks.repository import TasksSQLAlchemyRepository
from src.tasks.service import TasksService

http_bearer = HTTPBearer()


def get_auth_service() -> AuthService:
    """Dependency для получения сервиса авторизации"""
    uow = UnitOfWork(db_helper.session_factory)
    user_repository = UserRepository()
    auth_repository = AuthRepository()
    return AuthService(
        uow=uow,
        user_repository=user_repository,
        auth_repository=auth_repository,
    )


def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict:
    token = credentials.credentials
    payload = decode_jwt(token)
    exp = payload["exp"]
    if exp < datetime.now(UTC).timestamp():
        raise TokenExpiredError()
    return payload


async def get_token_for_refresh(
    request: Request,
) -> str:
    token = request.cookies.get("refresh_token")
    if token:
        return token
    raise InvalidTokenError("No token")


async def get_current_user(
    payload: dict = Depends(get_current_token_payload),
    service: AuthService = Depends(get_auth_service),
) -> UserDTO:
    """Получить текущего пользователя из токена"""
    token_type = payload.get(settings.auth.token_type_field)
    if token_type != settings.auth.access_token_field:
        raise InvalidTokenError("Invalid token type")
    email = payload.get("sub")
    if not email:
        raise InvalidTokenError("No email in token")
    user = await service.get_by_email(email)
    return user


async def get_current_active_user(
    user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    if user.is_deleted:
        raise ForbiddenError(
            detail="User deleted",
        )
    return user


async def get_current_verified_user(
    user: UserDTO = Depends(get_current_active_user),
) -> UserDTO:
    """Проверяет что пользователь верифицировал email"""
    if not user.is_verified:
        raise ForbiddenError(
            "Email not verified. Please verify your email address.",
        )
    return user


async def get_current_superuser(
    user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """Проверяет что пользователь является суперпользователем"""
    if not user.is_superuser:
        raise NoAccessError()
    return user


def get_task_service() -> TasksService:
    """Dependency для получения сервиса задач"""
    redis_repo = TasksRedisClient(settings.redis, redis_client.get_connection())
    jobs_redis_cli = JobsRedisClient(settings.redis, redis_client.get_connection())
    sqla_repo = TasksSQLAlchemyRepository()
    uow = UnitOfWork(db_helper.session_factory)
    return TasksService(
        tasks_redis_cli=redis_repo,
        jobs_redis_cli=jobs_redis_cli,
        sqla_repository=sqla_repo,
        uow=uow,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

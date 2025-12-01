from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Task


class TasksSQLAlchemyRepository:

    @classmethod
    async def save(cls, session: AsyncSession, data: dict):
        session.add(Task(**data))
        await session.commit()

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: UUID) -> Task | None:
        return await session.get(Task, id)

    @classmethod
    async def get_by_user_id(cls, session: AsyncSession, user_id: UUID) -> list[Task]:
        result = await session.scalars(select(Task).where(Task.user_id == user_id))
        return list(result.all())

    @classmethod
    async def delete(cls, session: AsyncSession, id: UUID) -> None:
        await session.execute(delete(Task).where(Task.id == id))

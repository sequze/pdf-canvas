from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Task


class TasksSQLAlchemyRepository:
    """Repository for Task model"""

    async def save(self, session: AsyncSession, data: dict):
        session.add(Task(**data))

    async def get_by_id(self, session: AsyncSession, id: UUID) -> Task | None:
        return await session.get(Task, id)

    async def get_by_user_id(self, session: AsyncSession, user_id: UUID) -> list[Task]:
        result = await session.scalars(select(Task).where(Task.user_id == user_id))
        return list(result.all())

    async def delete(self, session: AsyncSession, id: UUID) -> None:
        await session.execute(delete(Task).where(Task.id == id))

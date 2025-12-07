from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import User


class UserRepository:
    """Repository for User model"""
    @staticmethod
    def _filter_deleted(query: Select) -> Select:
        return query.filter(User.is_deleted == False)

    @classmethod
    async def create(cls, session: AsyncSession, data: dict) -> User:
        """Create new user"""
        user = User(**data)
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> User | None:
        """Get user by ID"""
        res = await session.execute(cls._filter_deleted(select(User).where(User.id == user_id)))
        return res.scalar_one_or_none()

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> User | None:
        """Get user by email"""
        stmt = cls._filter_deleted(select(User).where(User.email == email))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def update(cls, session: AsyncSession, user: User, data: dict) -> User:
        """Update user"""
        for key, value in data.items():
            setattr(user, key, value)
        await session.flush()
        await session.refresh(user)
        return user

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> None:
        """Delete user (soft delete)"""
        user = await cls.get_by_id(session, user_id)
        if user:
            user.is_deleted = True
            await session.flush()


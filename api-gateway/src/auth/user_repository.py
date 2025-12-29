from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import User


class UserRepository:
    """Repository for User model"""

    def _filter_deleted(self, query: Select) -> Select:
        return query.filter(User.is_deleted == False)

    async def create(self, session: AsyncSession, data: dict) -> User:
        """Create new user"""
        user = User(**data)
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        """Get user by ID"""
        res = await session.execute(self._filter_deleted(select(User).where(User.id == user_id)))
        return res.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Get user by email"""
        stmt = self._filter_deleted(select(User).where(User.email == email))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, session: AsyncSession, user: User, data: dict) -> User:
        """Update user"""
        for key, value in data.items():
            setattr(user, key, value)
        await session.flush()
        await session.refresh(user)
        return user

    async def delete(self, session: AsyncSession, user_id: UUID) -> None:
        """Delete user (soft delete)"""
        user = await self.get_by_id(session, user_id)
        if user:
            user.is_deleted = True
            await session.flush()

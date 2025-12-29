from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import delete, select
from src.core.models.refresh_session import RefreshSession


class AuthRepository:
    """Repository for managing refresh sessions"""

    async def create(self, session: AsyncSession, data: dict) -> RefreshSession:
        """Create refresh session"""
        token = RefreshSession(**data)
        session.add(token)
        await session.flush()
        await session.refresh(token)
        return token

    async def get_by_filters(self, session: AsyncSession, filters: dict) -> RefreshSession | None:
        """Get session by filters"""
        stmt = select(RefreshSession).filter_by(**filters)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_multi(self, session: AsyncSession, **filters):
        """Delete multiple sessions by filters"""
        stmt = delete(RefreshSession).filter_by(**filters)
        await session.execute(stmt)
        await session.flush()

    async def delete_by_token(self, session: AsyncSession, token: str):
        """Delete session by token"""
        stmt = delete(RefreshSession).filter_by(refresh_token=token)
        await session.execute(stmt)
        await session.flush()

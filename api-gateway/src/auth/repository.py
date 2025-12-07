from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import delete, select
from src.core.models.refresh_session import RefreshSession


class AuthRepository:
    model = RefreshSession

    @classmethod
    async def create(cls, session: AsyncSession, data: dict) -> RefreshSession:
        """Create refresh session"""
        token = RefreshSession(**data)
        session.add(token)
        await session.flush()
        await session.refresh(token)
        return token

    @classmethod
    async def get_by_filters(cls, session: AsyncSession, filters: dict) -> RefreshSession | None:
        """Get session by filters"""
        stmt = select(RefreshSession).filter_by(**filters)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def delete_multi(cls, session: AsyncSession, **filters):
        """Delete multiple sessions by filters"""
        stmt = delete(RefreshSession).filter_by(**filters)
        await session.execute(stmt)
        await session.flush()

    @classmethod
    async def delete_by_token(cls, session: AsyncSession, token: str):
        """Delete session by token"""
        stmt = delete(RefreshSession).filter_by(refresh_token=token)
        await session.execute(stmt)
        await session.flush()

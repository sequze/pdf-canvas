import asyncio
from sqlalchemy.ext.asyncio.session import AsyncSession
from uuid import uuid4, UUID
from datetime import datetime, UTC

from shared import UnitOfWork
from src.core.models import User
from src.core.config import settings
from .repository import AuthRepository
from .send_email import verify_verification_token, send_verification_email
from .user_repository import UserRepository
from .utils import decode_jwt, encode_jwt, verify_password, get_password_hash
from .schemas import LoginSchema, RegisterSchema, UserDTO
from .token import Token
from src.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    EmailNotExistsError,
    InvalidPasswordError,
    EmailAlreadyExistsError,
    ForbiddenError,
)


class AuthService:
    def __init__(
        self,
        uow: UnitOfWork,
        user_repository: UserRepository,
        auth_repository: AuthRepository,
    ):
        self.uow = uow
        self.user_repository = user_repository
        self.auth_repository = auth_repository

    def _create_token(self, payload: dict, token_type: str, expire_minutes: int) -> str:
        """Create JWT token"""
        jwt_payload = {settings.auth.token_type_field: token_type}
        jwt_payload.update(payload)
        return encode_jwt(jwt_payload, expire_minutes)

    def _create_refresh_token(self, email: str) -> str:
        """Create refresh token"""
        payload = {
            "sub": email,
            "jti": str(uuid4()),
        }
        return self._create_token(
            payload,
            settings.auth.refresh_token_field,
            settings.auth.refresh_token_expire_days * 60 * 24,
        )

    def _create_access_token(self, user: User) -> str:
        """Create access token"""
        payload = {
            "sub": str(user.email),
            "user_id": str(user.id),
        }
        return self._create_token(
            payload,
            settings.auth.access_token_field,
            settings.auth.access_token_expire_minutes,
        )

    async def _create_tokens(
        self,
        session: AsyncSession,
        user_id: UUID,
        user: User | None = None,
    ) -> Token:
        """Create token pair (access + refresh)"""
        if not user:
            user = await self.user_repository.get_by_id(session, user_id)
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(str(user.email))
        data = {"refresh_token": refresh_token, "user_id": user_id}
        await self.auth_repository.create(session, data)
        await session.commit()
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            type="Bearer",
        )

    async def register(self, data: RegisterSchema) -> Token:
        """Register new user"""
        async with self.uow as uow:
            existing_user = await self.user_repository.get_by_email(
                uow.session, str(data.email)
            )
            if existing_user:
                raise EmailAlreadyExistsError()

            user_data = {
                "email": str(data.email),
                "password_hash": get_password_hash(data.password),
                "is_verified": False,
                "is_deleted": False,
                "is_superuser": False,
            }
            user = await self.user_repository.create(uow.session, user_data)
            await uow.commit()
            asyncio.create_task(send_verification_email(data.email))
            return await self._create_tokens(uow.session, user.id, user)

    async def login(self, data: LoginSchema) -> Token:
        """User login"""
        async with self.uow as uow:
            user = await self.user_repository.get_by_email(uow.session, str(data.email))
            if not user:
                raise EmailNotExistsError()
            if not verify_password(data.password, user.password_hash):
                raise InvalidPasswordError()
            return await self._create_tokens(uow.session, user.id, user)

    async def create_token(self, user_id: UUID) -> Token:
        """Create token for user by ID"""
        async with self.uow as uow:
            return await self._create_tokens(uow.session, user_id)

    async def logout(self, refresh_token: str) -> None:
        """User logout (delete refresh token)"""
        async with self.uow as uow:
            await self.auth_repository.delete_by_token(uow.session, refresh_token)
            await uow.commit()

    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh tokens using refresh token"""
        async with self.uow as uow:
            token = await self.auth_repository.get_by_filters(
                uow.session,
                {"refresh_token": refresh_token},
            )
            if token is None:
                raise InvalidTokenError()

            payload = decode_jwt(token.refresh_token)
            if (
                payload.get(settings.auth.token_type_field)
                != settings.auth.refresh_token_field
            ):
                raise InvalidTokenError()

            email = payload["sub"]
            user = await self.user_repository.get_by_email(uow.session, email)
            if not user:
                raise InvalidTokenError()

            expires_in = payload["exp"]
            if datetime.now(UTC).timestamp() >= expires_in:
                raise TokenExpiredError()

            await uow.session.delete(token)
            await uow.commit()
            return await self._create_tokens(uow.session, user.id, user)

    async def abort_all_sessions(self, user_id: UUID) -> None:
        """Terminate all user sessions"""
        async with self.uow as uow:
            await self.auth_repository.delete_multi(
                session=uow.session, user_id=user_id
            )
            await uow.commit()

    async def change_password(
        self, email: str, old_password: str, new_password: str
    ) -> None:
        """Change user password"""
        async with self.uow as uow:
            user = await self.user_repository.get_by_email(uow.session, email)
            if not user:
                raise EmailNotExistsError()
            if not verify_password(old_password, user.password_hash):
                raise InvalidPasswordError()
            user.password_hash = get_password_hash(new_password)
            await uow.commit()

    async def get_by_email(self, email: str) -> UserDTO:
        """Get user by email"""
        async with self.uow as uow:
            user = await self.user_repository.get_by_email(uow.session, email)
            if not user:
                raise EmailNotExistsError()
            return UserDTO.model_validate(user)

    async def verify_account(self, token: str):
        async with self.uow as uow:
            payload = verify_verification_token(token)
            if payload is None:
                raise InvalidTokenError

            email = payload["sub"]
            user = await self.user_repository.get_by_email(uow.session, email)
            if user is None:
                raise InvalidTokenError

            expires_in = payload["exp"]
            if datetime.now().timestamp() >= expires_in:
                raise TokenExpiredError

            user.is_verified = True
            await uow.commit()

    async def send_verify_email(self, email: str):
        async with self.uow as uow:
            user = await self.user_repository.get_by_email(uow.session, email)
            if user is None:
                raise EmailNotExistsError
            if user.is_verified:
                raise ForbiddenError("You are already verified")
        asyncio.create_task(send_verification_email(email))

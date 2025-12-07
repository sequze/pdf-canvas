"""
Auth API endpoints
"""


from fastapi import APIRouter, Depends, Response, status

from src.auth.schemas import LoginSchema, RegisterSchema, UserDTO
from src.auth.service import AuthService
from src.auth.token import Token
from src.core.dependencies import (
    get_auth_service,
    get_current_user,
    get_current_active_user,
    get_token_for_refresh,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterSchema,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """Register new user"""
    return await service.register(data)


@router.post("/login", response_model=Token)
async def login(
    data: LoginSchema,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """User login"""
    token = await service.login(data)
    # Save refresh token in httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days
    )
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str = Depends(get_token_for_refresh),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """User logout"""
    await service.logout(refresh_token)
    response.delete_cookie("refresh_token")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: str = Depends(get_token_for_refresh),
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """Refresh tokens"""
    token = await service.refresh_token(refresh_token)
    # Update refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
    )
    return token


@router.get("/me", response_model=UserDTO)
async def get_me(
    user: UserDTO = Depends(get_current_active_user),
) -> UserDTO:
    """Get current user information"""
    return user


@router.post("/abort-sessions", status_code=status.HTTP_204_NO_CONTENT)
async def abort_all_sessions(
    user: UserDTO = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """Terminate all active user sessions"""
    await service.abort_all_sessions(user.id)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    old_password: str,
    new_password: str,
    user: UserDTO = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> None:
    """Change user password"""

    await service.change_password(str(user.email), old_password, new_password)

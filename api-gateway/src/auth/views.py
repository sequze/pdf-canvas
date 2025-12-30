from fastapi import APIRouter, Depends, Response, status, Request
from fastapi.responses import HTMLResponse
from src.core.limiter import limiter
from .schemas import LoginSchema, RegisterSchema, UserDTO
from .token import Token
from src.core.dependencies import (
    get_current_user,
    get_current_active_user,
    get_token_for_refresh, AuthServiceDep,
)
from src.core.config import settings
from ..core.exceptions import InvalidTokenError, TokenExpiredError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterSchema,
    service: AuthServiceDep,
) -> Token:
    """Register new user"""
    res = await service.register(data)
    return res


@router.post("/login", response_model=Token)
async def login(
    data: LoginSchema,
    response: Response,
    service: AuthServiceDep,
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
        max_age=settings.auth.refresh_token_cookie_max_age,
    )
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    service: AuthServiceDep,
    refresh_token: str = Depends(get_token_for_refresh),
) -> None:
    """User logout"""
    await service.logout(refresh_token)
    response.delete_cookie("refresh_token")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    service: AuthServiceDep,
    refresh_token: str = Depends(get_token_for_refresh),
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
        max_age=settings.auth.refresh_token_cookie_max_age,
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
    service: AuthServiceDep,
    user: UserDTO = Depends(get_current_user),
) -> None:
    """Terminate all active user sessions"""
    await service.abort_all_sessions(user.id)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    old_password: str,
    new_password: str,
    service: AuthServiceDep,
    user: UserDTO = Depends(get_current_user),
) -> None:
    """Change user password"""

    await service.change_password(str(user.email), old_password, new_password)


@router.get("/verify", response_class=HTMLResponse)
async def verify_account(
    token: str,
    service: AuthServiceDep,
):
    try:
        await service.verify_account(token)
        return "<h3>Ваш аккаунт успешно подтверждён ✅</h3>"
    except (InvalidTokenError, TokenExpiredError):
        return "<h3>Неверная или просроченная ссылка</h3>"

@router.get("/send-verification-email")
@limiter.limit("1/3minute")
async def send_verify_email(
        request: Request,
        service: AuthServiceDep,
        user: UserDTO = Depends(get_current_user),
):
    """Send verification email"""
    await service.send_verify_email(user.email)
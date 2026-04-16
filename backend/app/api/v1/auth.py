"""
Auth routes: register, login, refresh token, logout, and current user.

Tokens are delivered as httpOnly cookies rather than JSON body so they
are inaccessible to JavaScript (mitigates XSS token theft).
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth import authenticate_user, register_user, refresh_tokens

router = APIRouter()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """
    Write access and refresh tokens as httpOnly cookies on the response.

    Args:
        response: The FastAPI Response object to attach cookies to.
        access_token: The short-lived JWT access token.
        refresh_token: The long-lived JWT refresh token.
    """
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,       # HTTPS only — set False for local dev if needed
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new coach or client account.

    Sets httpOnly auth cookies on success so the client is immediately authenticated.
    """
    user = await register_user(db, data)
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    refresh_token = create_refresh_token(subject=str(user.id))
    _set_auth_cookies(response, access_token, refresh_token)
    return user


@router.post("/login", response_model=UserResponse)
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate an existing user and issue auth cookies.
    """
    user = await authenticate_user(db, data.email, data.password)
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    refresh_token = create_refresh_token(subject=str(user.id))
    _set_auth_cookies(response, access_token, refresh_token)
    return user


@router.post("/logout")
async def logout(response: Response):
    """
    Log the current user out by clearing both auth cookies.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=UserResponse)
async def refresh(
    response: Response,
    refresh_token: str = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Issue a new access token and refresh token using the existing refresh token cookie.

    Both tokens are rotated on each call. Returns the current user's profile.
    Returns 401 if the refresh token is missing, invalid, expired, or the wrong type.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    user = await refresh_tokens(db, refresh_token)
    new_access_token = create_access_token(subject=str(user.id), role=user.role.value)
    new_refresh_token = create_refresh_token(subject=str(user.id))
    _set_auth_cookies(response, new_access_token, new_refresh_token)
    return user


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    Used by the frontend on load to restore session state.
    """
    return current_user

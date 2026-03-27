"""
FastAPI dependency functions for auth and database session injection.

These are injected into route handlers via Depends(). Centralising them here
means auth logic is written once and enforced consistently across all routes.
"""

from typing import AsyncGenerator

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session and ensure it is closed after the request.

    Usage:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    access_token: str = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the current user from the access_token cookie.

    Args:
        access_token: The JWT access token read from the httpOnly cookie.
        db: Injected async database session.

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException 401: If the token is missing, invalid, expired, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    if not access_token:
        raise credentials_exception

    try:
        payload = decode_token(access_token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def require_coach(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that enforces the current user is a coach.

    Raises:
        HTTPException 403: If the current user is a client.
    """
    if current_user.role.value != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coach access required",
        )
    return current_user


async def require_client(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that enforces the current user is a client.

    Raises:
        HTTPException 403: If the current user is a coach.
    """
    if current_user.role.value != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client access required",
        )
    return current_user

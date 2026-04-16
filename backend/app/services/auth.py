"""
Authentication service: user registration and login business logic.

Route handlers in api/v1/auth.py call these functions — keeping the
business logic out of the route layer makes it easier to test and reuse.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jose import JWTError

from app.core.security import hash_password, verify_password, decode_token
from app.models.user import User
from app.schemas.user import UserCreate


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    """
    Register a new user account.

    Args:
        db: Async database session.
        data: Validated registration data (email, name, password, role).

    Returns:
        The newly created User ORM object.

    Raises:
        HTTPException 400: If the email address is already registered.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """
    Verify login credentials and return the authenticated user.

    Args:
        db: Async database session.
        email: The submitted email address.
        password: The submitted plaintext password.

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException 401: If no user with that email exists, or the password is wrong.
            Both cases return the same error to avoid email enumeration.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Deliberate: same error for wrong email vs wrong password (prevents enumeration)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return user


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> User:
    """
    Validate a refresh token and return the associated user.

    Args:
        db: Async database session.
        refresh_token: The JWT refresh token string from the cookie.

    Returns:
        The User associated with the token.

    Raises:
        HTTPException 401: If the token is invalid, expired, or the wrong type.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception

    return user

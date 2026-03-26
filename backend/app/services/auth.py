"""
Authentication service: user registration and login business logic.

Route handlers in api/v1/auth.py call these functions — keeping the
business logic out of the route layer makes it easier to test and reuse.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
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

"""
User management service: business logic for coach-client relationship operations.

Route handlers in api/v1/users.py call these functions — keeping business logic
out of the route layer makes it easier to test and reuse.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def add_client_by_email(db: AsyncSession, coach: User, email: str) -> User:
    """
    Link a client account to a coach by the client's email address.

    Args:
        db: Async database session.
        coach: The authenticated coach performing the action.
        email: Email address of the client account to link.

    Returns:
        The linked client User.

    Raises:
        HTTPException 404: If no client account exists with that email.
            The same error is returned when the email belongs to a coach, to
            avoid leaking role information.
        HTTPException 400: If the client is already on this coach's roster.
    """
    result = await db.execute(select(User).where(User.email == email))
    client = result.scalar_one_or_none()

    # Same error for "not found" and "wrong role" — avoids leaking role info
    if not client or client.role != UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if client in coach.clients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client already added",
        )

    coach.clients.append(client)
    await db.commit()
    await db.refresh(client)
    return client

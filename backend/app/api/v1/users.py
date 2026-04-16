"""
User management routes: coach-client relationship management.

Coaches use these endpoints to view and add clients to their roster.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_coach
from app.models.user import User, coach_client
from app.schemas.user import UserResponse, ClientByEmailRequest
from app.services.users import add_client_by_email as add_client_by_email_service

router = APIRouter()


@router.get("/clients", response_model=List[UserResponse])
async def get_my_clients(
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Return all clients linked to the authenticated coach.

    Only accessible by coaches.
    """
    result = await db.execute(
        select(User)
        .join(coach_client, User.id == coach_client.c.client_id)
        .where(coach_client.c.coach_id == coach.id)
    )
    return result.scalars().all()


@router.post("/clients/by-email", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_client_by_email(
    data: ClientByEmailRequest,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Link a client to this coach's roster by email address.

    Args:
        data: Request body containing the client's email address.

    Raises:
        HTTPException 404: If no client account exists with that email.
        HTTPException 400: If the client is already on this coach's roster.
        HTTPException 403: If the caller is not a coach.
    """
    return await add_client_by_email_service(db, coach, data.email)


@router.post("/clients/{client_id}", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Link an existing client account to the authenticated coach.

    Args:
        client_id: UUID of the client account to add.

    Raises:
        HTTPException 404: If the user does not exist or is not a client.
        HTTPException 400: If the client is already linked to this coach.
    """
    result = await db.execute(select(User).where(User.id == client_id))
    client = result.scalar_one_or_none()

    if not client or client.role.value != "client":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if client in coach.clients:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client already added")

    coach.clients.append(client)
    await db.commit()
    return client


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(require_coach),
):
    """
    Remove a client from the authenticated coach's roster.

    Args:
        client_id: UUID of the client to remove.

    Raises:
        HTTPException 404: If the client is not on this coach's roster.
    """
    result = await db.execute(select(User).where(User.id == client_id))
    client = result.scalar_one_or_none()

    if not client or client not in coach.clients:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found on your roster")

    coach.clients.remove(client)
    await db.commit()

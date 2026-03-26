"""
Messaging routes: send and retrieve direct messages between a coach and client.

Messages are scoped to a two-user thread. Fetching a thread automatically
marks incoming unread messages as read.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter()


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a direct message to another user.

    Args:
        data: Contains recipient_id and message content.

    Raises:
        HTTPException 404: If the recipient does not exist.
        HTTPException 400: If the user tries to message themselves.
    """
    if data.recipient_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot message yourself")

    result = await db.execute(select(User).where(User.id == data.recipient_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    message = Message(
        sender_id=current_user.id,
        recipient_id=data.recipient_id,
        content=data.content,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/{other_user_id}", response_model=List[MessageResponse])
async def get_conversation(
    other_user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the full message thread between the current user and another user,
    ordered chronologically.

    Also marks any unread incoming messages as read (sets read_at to now).

    Args:
        other_user_id: UUID of the other participant in the conversation.

    Raises:
        HTTPException 404: If the other user does not exist.
    """
    result = await db.execute(select(User).where(User.id == other_user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.recipient_id == current_user.id),
            )
        )
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    # Mark incoming unread messages as read
    now = datetime.utcnow()
    for msg in messages:
        if msg.recipient_id == current_user.id and msg.read_at is None:
            msg.read_at = now
    await db.commit()

    return messages


@router.get("/", response_model=List[MessageResponse])
async def get_recent_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the most recent message from each conversation the current user is part of.

    Useful for rendering an inbox/conversation list view.
    """
    result = await db.execute(
        select(Message)
        .where(
            or_(
                Message.sender_id == current_user.id,
                Message.recipient_id == current_user.id,
            )
        )
        .order_by(Message.created_at.desc())
    )
    all_messages = result.scalars().all()

    # Deduplicate: keep only the latest message per conversation partner
    seen: set[uuid.UUID] = set()
    conversations: List[Message] = []
    for msg in all_messages:
        other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        if other_id not in seen:
            seen.add(other_id)
            conversations.append(msg)

    return conversations

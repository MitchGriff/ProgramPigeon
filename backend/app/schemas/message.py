"""
Pydantic schemas for direct messages between coaches and clients.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageCreate(BaseModel):
    """Request body for sending a message."""
    recipient_id: uuid.UUID
    content: str


class MessageResponse(BaseModel):
    """Message data returned from the API."""
    id: uuid.UUID
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    content: str
    created_at: datetime
    read_at: Optional[datetime]  # None until the recipient reads the message

    model_config = {"from_attributes": True}

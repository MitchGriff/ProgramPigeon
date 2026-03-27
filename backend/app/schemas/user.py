"""
Pydantic schemas for user-related API inputs and outputs.

Never return raw ORM User objects from endpoints — always use UserResponse
so the password hash is never accidentally serialised.
"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    """The two account types. Mirrors the ORM enum."""
    coach = "coach"
    client = "client"


class UserCreate(BaseModel):
    """Request body for POST /auth/register."""
    email: EmailStr
    name: str
    password: str
    role: UserRole


class UserLogin(BaseModel):
    """Request body for POST /auth/login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Public-facing user data returned from API endpoints.
    Never includes the password hash.
    """
    id: uuid.UUID
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}

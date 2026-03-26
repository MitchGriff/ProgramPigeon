"""
Pydantic schemas for JWT token responses.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Returned after a successful login or register — wraps the access token."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload fields."""
    sub: str    # User ID
    role: str   # 'coach' or 'client'
    type: str   # 'access' or 'refresh'

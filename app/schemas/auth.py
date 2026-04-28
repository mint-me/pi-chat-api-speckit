"""Authentication request and response schemas."""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response body for a user resource."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str


class TokenResponse(BaseModel):
    """Response body for successful authentication."""

    access_token: str
    token_type: str = "bearer"

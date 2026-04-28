"""Password hashing and JWT utilities."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import get_settings

_password_hash = PasswordHash.recommended()


def normalize_email(email: str) -> str:
    """Return a normalized email address for storage and lookup."""
    return email.strip().lower()


def hash_password(plain: str) -> str:
    """Hash a plain-text password with Argon2."""
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against an Argon2 hash."""
    return _password_hash.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a signed JWT access token for the given user."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("invalid token type")
    return uuid.UUID(str(payload["sub"]))

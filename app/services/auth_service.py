"""Authentication business logic."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import AppError
from app.models import User
from app.security import hash_password, normalize_email, verify_password


async def register_user(session: AsyncSession, email: str, password: str) -> User:
    """Create a user account."""
    normalized_email = normalize_email(email)
    existing = await session.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise AppError(status_code=409, detail="Email already registered")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        created_at=datetime.now(UTC),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(status_code=409, detail="Email already registered") from exc
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    """Validate a user's credentials."""
    normalized_email = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(status_code=401, detail="Invalid email or password")
    return user

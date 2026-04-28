"""Seed demo data into the configured database."""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.config import get_settings
from app.database import configure_database, get_session_factory
from app.models import Conversation, Message, User
from app.security import hash_password, normalize_email


async def main() -> int:
    """Create a demo account and sample conversation if absent."""
    settings = get_settings()
    configure_database(settings.database_url)
    session_factory = get_session_factory()
    async with session_factory() as session:
        email = normalize_email("demo@example.com")
        user = await session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password("password123"),
                created_at=datetime.now(UTC),
            )
            session.add(user)
            await session.flush()

            now = datetime.now(UTC)
            conversation = Conversation(
                user_id=user.id,
                title="Demo conversation",
                created_at=now,
                updated_at=now,
            )
            session.add(conversation)
            await session.flush()
            session.add(
                Message(
                    conversation_id=conversation.id,
                    role="user",
                    content="Hello from the seeded demo account.",
                    created_at=now,
                )
            )
            session.add(
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content="Hello. This is a seeded conversation.",
                    created_at=now,
                    provider_metadata={"provider": "seed", "model": "seed"},
                )
            )
            conversation.updated_at = now
            await session.commit()
            print("Seeded demo@example.com / password123")
            return 0

        print("Demo user already exists; seed skipped")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

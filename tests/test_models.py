"""Smoke tests for ORM behavior."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import Conversation, Message, User


async def test_tables_created(db_session):
    result = await db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = {row[0] for row in result.fetchall()}
    assert {"users", "conversations", "messages"}.issubset(tables)


async def test_user_email_unique(db_session):
    now = datetime.now(UTC)
    db_session.add(
        User(id=uuid.uuid4(), email="dup@example.com", password_hash="a", created_at=now)
    )
    await db_session.flush()
    db_session.add(
        User(id=uuid.uuid4(), email="dup@example.com", password_hash="b", created_at=now)
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_conversation_cascades_on_user_delete(db_session):
    now = datetime.now(UTC)
    user = User(id=uuid.uuid4(), email="u@example.com", password_hash="a", created_at=now)
    db_session.add(user)
    await db_session.flush()
    convo = Conversation(
        id=uuid.uuid4(),
        user_id=user.id,
        title="hello",
        created_at=now,
        updated_at=now,
    )
    db_session.add(convo)
    await db_session.flush()
    message = Message(
        id=uuid.uuid4(),
        conversation_id=convo.id,
        role="user",
        content="hi",
        created_at=now,
    )
    db_session.add(message)
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    conversations = await db_session.execute(text("SELECT COUNT(*) FROM conversations"))
    messages = await db_session.execute(text("SELECT COUNT(*) FROM messages"))
    assert conversations.scalar() == 0
    assert messages.scalar() == 0

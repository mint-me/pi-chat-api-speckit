"""Chat business logic."""

import json
import logging
import uuid
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime
from textwrap import shorten
from time import monotonic

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.errors import AppError
from app.models import Conversation, Message, User
from app.services.llm import LLMClient, ProviderError

logger = logging.getLogger(__name__)


def _conversation_title(message: str) -> str:
    return shorten(" ".join(message.split()), width=255, placeholder="...")


async def _get_owned_conversation(
    session: AsyncSession, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation:
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    )
    conversation = await session.scalar(statement)
    if conversation is None:
        raise AppError(status_code=404, detail="Conversation not found")
    return conversation


async def prepare_chat(
    session: AsyncSession,
    user: User,
    message: str,
    conversation_id: uuid.UUID | None,
) -> tuple[Conversation, list[dict[str, str]]]:
    """Persist the user message and return the conversation plus prompt messages."""
    if conversation_id is None:
        conversation = Conversation(
            user_id=user.id,
            title=_conversation_title(message),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(conversation)
        await session.flush()
        prior_messages: list[dict[str, str]] = []
    else:
        conversation = await _get_owned_conversation(session, user.id, conversation_id)
        result = await session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
        )
        prior_messages = [{"role": item.role, "content": item.content} for item in result]

    now = datetime.now(UTC)
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message,
        created_at=now,
    )
    session.add(user_message)
    conversation.updated_at = now
    if conversation_id is None:
        conversation.title = _conversation_title(message)
    await session.commit()
    return conversation, [*prior_messages, {"role": "user", "content": message}]


async def stream_assistant_response(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    llm_client: LLMClient,
    prompt_messages: Sequence[dict[str, str]],
) -> AsyncIterator[str]:
    """Stream assistant chunks and persist the completed assistant message."""
    start = monotonic()
    chunks: list[str] = []
    chunk_count = 0

    try:
        async for chunk in llm_client.stream(prompt_messages):
            if not chunk:
                continue
            chunks.append(chunk)
            chunk_count += 1
            yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
    except ProviderError as exc:
        latency_ms = int((monotonic() - start) * 1000)
        logger.info(
            "chat.llm_error",
            extra={
                "event": "chat.llm_error",
                "provider": llm_client.name,
                "model": llm_client.model,
                "error_class": exc.__class__.__name__,
                "latency_ms": latency_ms,
            },
        )
        yield f"event: error\ndata: {json.dumps({'detail': 'provider unavailable'})}\n\n"
        return
    except Exception as exc:  # pragma: no cover - defensive guard
        latency_ms = int((monotonic() - start) * 1000)
        logger.exception(
            "chat.llm_error",
            extra={
                "event": "chat.llm_error",
                "provider": llm_client.name,
                "model": llm_client.model,
                "error_class": exc.__class__.__name__,
                "latency_ms": latency_ms,
            },
        )
        yield f"event: error\ndata: {json.dumps({'detail': 'unexpected error'})}\n\n"
        return

    assistant_text = "".join(chunks)
    async with session_factory() as session:
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise AppError(status_code=404, detail="Conversation not found")
        now = datetime.now(UTC)
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_text,
            provider_metadata={
                "provider": llm_client.name,
                "model": llm_client.model,
                "chunk_count": chunk_count,
            },
            created_at=now,
        )
        session.add(assistant_message)
        conversation.updated_at = now
        await session.commit()

    latency_ms = int((monotonic() - start) * 1000)
    logger.info(
        "chat.llm_done",
        extra={
            "event": "chat.llm_done",
            "provider": llm_client.name,
            "model": llm_client.model,
            "chunk_count": chunk_count,
            "latency_ms": latency_ms,
        },
    )
    yield f"event: done\ndata: {json.dumps({'conversation_id': str(conversation_id)})}\n\n"


async def get_history(
    session: AsyncSession,
    user: User,
    conversation_id: uuid.UUID | None = None,
) -> list[Conversation]:
    """Return the requested conversations for a user."""
    if conversation_id is not None:
        statement = (
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user.id)
            .options(selectinload(Conversation.messages))
        )
        conversation = await session.scalar(statement)
        if conversation is None:
            raise AppError(status_code=404, detail="Conversation not found")
        return [conversation]

    statement = (
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    result = await session.scalars(statement)
    return list(result.unique().all())

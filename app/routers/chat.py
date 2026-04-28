"""Chat routes."""

import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app import database
from app.config import get_settings
from app.deps import CurrentUserDep, SessionDep
from app.errors import AppError
from app.schemas.chat import ChatRequest, ConversationResponse, HistoryResponse
from app.services.chat_service import get_history, prepare_chat, stream_assistant_response
from app.services.llm import get_llm_client

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)
ConversationIdQuery = Annotated[uuid.UUID | None, Query()]


def _sse_error(detail: str) -> str:
    return f"event: error\ndata: {json.dumps({'detail': detail})}\n\n"


@router.post("")
async def chat(payload: ChatRequest, user: CurrentUserDep, session: SessionDep):
    """Stream an assistant response via SSE."""
    if database.SessionLocal is None:

        async def missing_db() -> AsyncIterator[str]:
            yield _sse_error("Database not initialized")

        return StreamingResponse(missing_db(), media_type="text/event-stream", status_code=500)

    try:
        conversation, prompt_messages = await prepare_chat(
            session=session,
            user=user,
            message=payload.message,
            conversation_id=payload.conversation_id,
        )
    except AppError as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    llm_client = get_llm_client(get_settings())

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for chunk in stream_assistant_response(
                session_factory=database.get_session_factory(),
                conversation_id=conversation.id,
                user_id=user.id,
                llm_client=llm_client,
                prompt_messages=prompt_messages,
            ):
                yield chunk
        except AppError as exc:
            logger.info("chat.error", extra={"event": "chat.error", "status_code": exc.status_code})
            yield _sse_error(exc.detail)
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("chat.error", extra={"event": "chat.error"})
            yield _sse_error("Unexpected server error")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history", response_model=HistoryResponse)
async def history(
    user: CurrentUserDep,
    session: SessionDep,
    conversation_id: ConversationIdQuery = None,
) -> HistoryResponse:
    """Return conversation history for the current user."""
    conversations = await get_history(session, user, conversation_id)
    return HistoryResponse(
        conversations=[
            ConversationResponse.model_validate(conversation) for conversation in conversations
        ]
    )

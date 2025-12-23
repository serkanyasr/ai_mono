"""Chat endpoints."""

import json
import uuid
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from src.utils import get_logger

from src.api.schemas import ChatRequest
from src.repositories import SessionRepository, MessageRepository
from src.chat.stream import StreamChat, StreamChatDeps

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat/stream")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        request_id = str(uuid.uuid4())
        logger.info(f"/chat/stream request_id={request_id} user_id={chat_request.user_id}")

        # Get agent service from app state
        agent_service = request.app.state.agent_service if hasattr(request.app.state, 'agent_service') else None
        if not agent_service:
            raise HTTPException(status_code=500, detail="Agent service not initialized")

        sessions_repo = SessionRepository()
        messages_repo = MessageRepository()

        chat = StreamChat(
            deps=StreamChatDeps(
                sessions=sessions_repo,
                messages=messages_repo,
                agent_service=agent_service,
            ),
            cache=request.app.state.agent_cache if hasattr(request.app.state, 'agent_cache') else None
        )

        async def generate_stream():
            try:
                yield f"data: {json.dumps({'type': 'request', 'request_id': request_id})}\n\n"
                async for item in chat.stream(
                    message=chat_request.message,
                    session_id=chat_request.session_id,
                    user_id=chat_request.user_id,
                    metadata=chat_request.metadata or {},
                ):
                    yield f"data: {json.dumps(item)}\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

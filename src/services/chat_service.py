"""Chat service for chat interaction business logic."""

from typing import AsyncIterator, Dict, Any, Optional

from .base_service import BaseService
from src.core.interfaces.repositories import ISessionRepository, IMessageRepository


class ChatService(BaseService):
    """Service for chat operations orchestration.

    This service coordinates between repositories, agent service, and cache
    to handle chat interactions including streaming responses.
    """

    def __init__(
        self,
        session_repository: ISessionRepository,
        message_repository: IMessageRepository,
        agent_service,
        cache=None
    ):
        """Initialize chat service.

        Args:
            session_repository: Session repository instance
            message_repository: Message repository instance
            agent_service: Agent service instance
            cache: Optional agent cache
        """
        super().__init__()
        self._session_repo = session_repository
        self._message_repo = message_repository
        self._agent_service = agent_service
        self._cache = cache

    async def get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: Optional[str],
        metadata: Dict[str, Any]
    ) -> str:
        """Get existing session or create new one.

        Args:
            session_id: Optional session ID to check
            user_id: User identifier for new session
            metadata: Optional metadata for new session

        Returns:
            Session ID
        """
        if session_id:
            session = await self._session_repo.get(session_id)
            if session:
                return session_id

        return await self._session_repo.create(
            user_id=user_id,
            metadata=metadata or {}
        )

    async def get_conversation_context(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> list[Dict[str, str]]:
        """Get conversation context for given session.

        Args:
            session_id: Session UUID
            max_messages: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with role and content
        """
        messages = await self._message_repo.list(session_id, limit=max_messages)
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def stream_chat(
        self,
        message: str,
        session_id: Optional[str],
        user_id: Optional[str],
        metadata: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute streaming chat interaction.

        Args:
            message: User message
            session_id: Optional session ID
            user_id: User identifier
            metadata: Optional metadata

        Yields:
            Dictionary with event type and data
        """
        try:
            # Get or create session
            current_session_id = await self.get_or_create_session(
                session_id, user_id, metadata
            )
            yield {"type": "session", "session_id": current_session_id}

            # Get conversation context
            context_messages = await self.get_conversation_context(current_session_id)

            agent_context = {
                "session_id": current_session_id,
                "user_id": user_id,
                "conversation_history": context_messages,
                "retrieved_documents": [],
                "metadata": metadata
            }

            # Save user message
            await self._message_repo.add(
                current_session_id,
                "user",
                message,
                {**metadata, "user_id": user_id}
            )

            # Get or create agent from cache
            if self._cache:
                agent = self._cache.get(current_session_id)
                if agent is None:
                    agent = await self._agent_service.create_agent({})
                    self._cache.set(current_session_id, agent)
            else:
                agent = await self._agent_service.create_agent({})

            # Stream agent response
            full_response = ""
            tools_used = []

            async for event in self._agent_service.stream_agent(agent, message, agent_context):
                if event["type"] == "text":
                    full_response += event["content"]
                    yield event
                elif event["type"] == "tools":
                    tools_used = event.get("tools", [])
                    yield event
                elif event["type"] == "error":
                    self._logger.error(f"Agent streaming error: {event['error']}")
                    yield event
                elif event["type"] == "end":
                    # Save assistant message
                    await self._message_repo.add(
                        current_session_id,
                        "assistant",
                        full_response,
                        {"streamed": True, "tool_calls": len(tools_used)}
                    )
                    yield {"type": "end"}

        except Exception as e:
            await self._handle_error(e, {
                "operation": "stream_chat",
                "user_id": user_id,
                "session_id": session_id
            })

"""Chat use cases."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.application.interfaces.repositories import ChatRepository
from app.domain.entities.entities import Conversation, ChatMessage
from app.agents import ChatAgent


class SendMessageUseCase:
    """Use case for sending a chat message and getting AI response."""

    def __init__(
        self,
        chat_repo: ChatRepository,
        chat_agent: Optional[ChatAgent] = None,
    ):
        self.chat_repo = chat_repo
        self.chat_agent = chat_agent or ChatAgent()

    async def execute(
        self,
        message: str,
        ipo_symbol: Optional[str] = None,
        conversation_id: Optional[str] = None,
        analysis_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a message and get AI response."""
        
        # Get or create conversation
        if conversation_id:
            conversation = await self.chat_repo.get_conversation(conversation_id)
            if not conversation:
                return {"error": "Conversation not found"}
        else:
            conversation = await self.chat_repo.create_conversation(
                title=message[:50],
                ipo_symbol=ipo_symbol,
            )
        
        # Add user message
        user_message = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
            metadata={"ipo_symbol": ipo_symbol} if ipo_symbol else {},
        )
        await self.chat_repo.add_message(user_message)
        
        # Get conversation history
        history = await self.chat_repo.get_messages(conversation_id=conversation.id, limit=10)
        
        # Create agent context
        from app.agents.base import AgentContext
        agent_context = AgentContext(
            ipo_symbol=ipo_symbol or "",
            analysis_id=uuid.uuid4(),
            parameters={"conversation_id": str(conversation.id)},
        )
        
        # Get AI response
        agent_input = {
            "message": message,
            "ipo_symbol": ipo_symbol,
            "conversation_history": [
                {
                    "role": m.role,
                    "content": m.content,
                    "agent": m.metadata.get("agent"),
                    "timestamp": m.timestamp.isoformat() if hasattr(m, 'timestamp') else str(m.timestamp),
                }
                for m in history
            ],
            "analysis_data": analysis_data or {},
        }
        
        result = await self.chat_agent.run_with_retry(agent_context, agent_input)
        
        if result.status.value != "completed":
            return {"error": result.error or "AI response failed"}
        
        ai_response_data = result.data
        
        # Add assistant message
        assistant_message = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response_data.get("message", ""),
            agent=ai_response_data.get("agent_used"),
            metadata={
                "sources": ai_response_data.get("sources", []),
                "confidence": ai_response_data.get("confidence", 0.8),
                "follow_up_questions": ai_response_data.get("follow_up_questions", []),
            },
        )
        await self.chat_repo.add_message(assistant_message)
        
        # Update conversation
        await self.chat_repo.update_conversation(
            conversation.id,
            updated_at=datetime.utcnow(),
        )
        
        return {
            "conversation_id": str(conversation.id),
            "user_message": {
                "id": str(user_message.id),
                "conversation_id": str(conversation.id),
                "role": "user",
                "content": message,
                "agent": None,
                "timestamp": user_message.timestamp.isoformat() if hasattr(user_message, 'timestamp') else str(user_message.timestamp),
                "metadata": user_message.metadata,
            },
            "assistant_message": {
                "id": str(assistant_message.id),
                "conversation_id": str(conversation.id),
                "role": "assistant",
                "content": ai_response_data.get("message", ""),
                "agent": ai_response_data.get("agent_used"),
                "timestamp": assistant_message.timestamp.isoformat() if hasattr(assistant_message, 'timestamp') else str(assistant_message.timestamp),
                "metadata": assistant_message.metadata,
            },
        }


class GetConversationUseCase:
    """Use case for getting a conversation."""

    def __init__(self, chat_repo: ChatRepository):
        self.chat_repo = chat_repo

    async def execute(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation with messages."""
        conversation = await self.chat_repo.get_conversation(conversation_id)
        if not conversation:
            return None
        
        messages = await self.chat_repo.get_messages(conversation_id=conversation_id)
        
        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "ipo_symbol": conversation.ipo_symbol,
            "created_at": conversation.created_at.isoformat() if hasattr(conversation, 'created_at') else str(conversation.created_at),
            "updated_at": conversation.updated_at.isoformat() if hasattr(conversation, 'updated_at') else str(conversation.updated_at),
            "message_count": len(messages),
            "messages": [
                {
                    "id": str(m.id),
                    "conversation_id": str(m.conversation_id),
                    "role": m.role,
                    "content": m.content,
                    "agent": m.metadata.get("agent"),
                    "timestamp": m.timestamp.isoformat() if hasattr(m, 'timestamp') else str(m.timestamp),
                    "metadata": m.metadata,
                }
                for m in messages
            ],
        }


class ListConversationsUseCase:
    """Use case for listing conversations."""

    def __init__(self, chat_repo: ChatRepository):
        self.chat_repo = chat_repo

    async def execute(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations."""
        conversations = await self.chat_repo.list_conversations(limit=limit, offset=offset)
        
        return [
            {
                "id": str(c.id),
                "title": c.title,
                "ipo_symbol": c.ipo_symbol,
                "created_at": c.created_at.isoformat() if hasattr(c, 'created_at') else str(c.created_at),
                "updated_at": c.updated_at.isoformat() if hasattr(c, 'updated_at') else str(c.updated_at),
                "message_count": c.message_count,
            }
            for c in conversations
        ]
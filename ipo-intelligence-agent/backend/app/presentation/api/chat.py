"""API router for Chat."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.application.use_cases.chat_use_case import (
    SendMessageUseCase,
    GetConversationUseCase,
    ListConversationsUseCase,
)
from app.infrastructure.repositories.sql_repositories import (
    SQLChatRepository,
)
from app.infrastructure.database.session import get_db_session
from app.core.config.settings import get_settings

router = APIRouter(tags=["Chat"])


# Dependency injection
async def get_chat_repo():
    async with get_db_session() as session:
        yield SQLChatRepository(session)


async def get_send_message_use_case(
    chat_repo=Depends(get_chat_repo),
) -> SendMessageUseCase:
    return SendMessageUseCase(chat_repo)


async def get_conversation_use_case(
    chat_repo=Depends(get_chat_repo),
) -> GetConversationUseCase:
    return GetConversationUseCase(chat_repo)


async def get_list_conversations_use_case(
    chat_repo=Depends(get_chat_repo),
) -> ListConversationsUseCase:
    return ListConversationsUseCase(chat_repo)


# Request/Response Models
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    ipo_symbol: Optional[str] = None
    conversation_id: Optional[str] = None
    analysis_data: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    agent: Optional[str] = None
    timestamp: str
    metadata: Dict[str, Any] = {}


class ConversationResponse(BaseModel):
    id: str
    title: str
    ipo_symbol: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int


class SendMessageResponse(BaseModel):
    conversation_id: str
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


@router.post("/send", response_model=SendMessageResponse, status_code=status.HTTP_200_OK)
async def send_message(
    request: ChatMessageRequest,
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
):
    """Send a message and get AI response."""
    result = await use_case.execute(
        message=request.message,
        ipo_symbol=request.ipo_symbol,
        conversation_id=request.conversation_id,
        analysis_data=request.analysis_data,
    )
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    
    return result


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    use_case: ListConversationsUseCase = Depends(get_list_conversations_use_case),
):
    """List chat conversations."""
    return await use_case.execute(limit=limit, offset=offset)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    use_case: GetConversationUseCase = Depends(get_conversation_use_case),
):
    """Get conversation with messages."""
    conversation = await use_case.execute(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    chat_repo=Depends(get_chat_repo),
):
    """Delete a conversation."""
    success = await chat_repo.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
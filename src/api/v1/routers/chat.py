from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from src.api.core.database import get_db
from src.api.dependencies import get_current_user
from src.api.services import ChatService, MessageService
from src.api.core.redis_client import get_redis
from src.models import User
from src.api.v1.schemas import (
    ChatSchema,
    ChatCreate,
    MessageSchema,
    SuccessResponse
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("", response_model=ChatSchema, status_code=201)
async def create_chat(
        data: ChatCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new chat for the current user.
    """
    chat_service = ChatService(db)
    chat = await chat_service.create_chat(
        user_id=current_user.id,
        title=data.title
    )
    return chat


@router.get("", response_model=List[ChatSchema])
async def get_user_chats(
        limit: int = Query(50, ge=1, le=100, description="Number of chats to return"),
        offset: int = Query(0, ge=0, description="Number of chats to skip"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Get all chats for the current user.
    Returns chats ordered by updated_at (most recent first).
    """
    chat_service = ChatService(db)
    chats = await chat_service.get_user_chats(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    return chats


@router.get("/{chat_id}", response_model=ChatSchema)
async def get_chat(
        chat_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Get a specific chat by ID.
    Returns 404 if chat doesn't exist.
    Returns 403 if chat doesn't belong to current user.
    """
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(
        chat_id=chat_id,
        user_id=current_user.id
    )
    return chat


@router.get("/{chat_id}/messages", response_model=List[MessageSchema])
async def get_chat_messages(
        chat_id: UUID,
        limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
        offset: int = Query(0, ge=0, description="Number of messages to skip"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Get message history for a chat.
    Returns messages in chronological order (oldest first).

    Note: For real-time chat, use WebSocket which provides cached recent messages.
    This endpoint is for pagination/history browsing.
    """
    # Verify user has access to this chat
    chat_service = ChatService(db)
    await chat_service.get_chat(chat_id=chat_id, user_id=current_user.id)

    # Get messages from DB
    redis = await get_redis()
    message_service = MessageService(db, redis)
    messages = await message_service.get_all_messages(
        chat_id=chat_id,
        limit=limit,
        offset=offset
    )

    return messages


@router.patch("/{chat_id}", response_model=ChatSchema)
async def update_chat(
        chat_id: UUID,
        data: ChatCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Update chat title.
    Returns 404 if chat doesn't exist.
    Returns 403 if chat doesn't belong to current user.
    """
    if not data.title:
        from src.api.exceptions import ValidationError
        raise ValidationError("Title is required for update")

    chat_service = ChatService(db)
    chat = await chat_service.update_chat_title(
        chat_id=chat_id,
        user_id=current_user.id,
        title=data.title
    )
    return chat


@router.delete("/{chat_id}", response_model=SuccessResponse)
async def delete_chat(
        chat_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Delete a chat and all its messages.
    Returns 404 if chat doesn't exist.
    Returns 403 if chat doesn't belong to current user.
    """
    chat_service = ChatService(db)
    await chat_service.delete_chat(
        chat_id=chat_id,
        user_id=current_user.id
    )

    return SuccessResponse(data={"message": "Chat deleted successfully"})

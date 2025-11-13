import json
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.domain.entity import UserEntity
from app.presentation.schemas.message_schemas import MessageCreate
from app.application.services.chat_service import ChatService
from app.application.services.dep import get_chat_service
from app.presentation.auth.auth import get_user_by_token
from app.infrastructure.ws.connection_manager import manager

chat_ws = APIRouter(tags=["Chat WS"], prefix="/ws/chat")


async def get_websocket_user(
    token: Annotated[
        str,
        Query(
            ...,
        ),
    ],
):
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен аутентификации",
        )
    return user


@chat_ws.websocket("/{room_id}")
async def send_message(
    websocket: WebSocket,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    user: Annotated[UserEntity, Depends(get_websocket_user)],
    chat_service: Annotated[ChatService,Depends(get_chat_service)],
):
    """
    Эндпоинт WebSocket для чата в комнате.
    """
    await manager.connect(room_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                text = message_data["text"]
            except (json.JSONDecodeError, KeyError):
                continue

            new_message = chat_service.create_message(
                room_id, user.id, MessageCreate(text=text)
            )

            new_message_json = new_message.model_dump_json()

            await manager.broadcast(room_id, new_message_json)

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(room_id, f"Пользователь {user.username} ушел")

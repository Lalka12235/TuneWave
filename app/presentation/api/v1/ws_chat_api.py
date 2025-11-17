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
from app.presentation.auth.auth import check_provider
from app.infrastructure.ws.connection_manager import manager
from app.infrastructure.db.repositories.dep import get_user_repo
from app.infrastructure.db.repositories.user_repo import SQLalchemyUserRepository

chat_ws = APIRouter(tags=["Chat WS"], prefix="/ws/chat")
user_repoitory = Annotated[SQLalchemyUserRepository,Depends(get_user_repo())]


async def get_websocket_user(
    token: Annotated[
        str,
        Query(
            ...,
        ),
    ],
    user_repo: user_repoitory
):
    auth_data = check_provider(token)
    if not auth_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен аутентификации",
        )
    external_id = auth_data["external_id"]
    provider = auth_data['provider']
    user = None
    if provider == "google":
        user = user_repo.get_user_by_google_id(external_id)

    elif provider == "spotify":
        user = user_repo.get_user_by_spotify_id(external_id)
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

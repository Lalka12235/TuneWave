import json
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Cookie,
    Path,
    WebSocket,
    WebSocketDisconnect,
)

from app.domain.entity import UserEntity
from app.application.services.chat_service import ChatService
from app.infrastructure.ws.connection_manager import manager

from dishka.integrations.fastapi import DishkaRoute,FromDishka,inject

chat_ws = APIRouter(tags=["Chat WS"], prefix="/ws/chat",route_class=DishkaRoute)
user_dependencies = FromDishka[UserEntity]
chat_service = FromDishka[ChatService]


@chat_ws.websocket("/{room_id}")
@inject
async def send_message(
    websocket: WebSocket,
    room_id: Annotated[uuid.UUID, Path(..., description="Уникальный ID комнаты")],
    user: user_dependencies,
    session_id: Annotated[str | None, Cookie()] = None,
    #chat_serv: chat_service,
):
    """
    Эндпоинт WebSocket для чата в комнате.
    """
    user.set_session_id = session_id
    user_from_identity = user.get_current_user()
    await manager.connect(room_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                message_data["text"]
            except (json.JSONDecodeError, KeyError):
                continue

            #new_message = chat_serv.create_message(
            #    room_id, user.id, MessageCreate(text=text)
            #)

            #new_message_json = new_message.model_dump_json()

            #await manager.broadcast(room_id, new_message_json)

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(room_id, f"Пользователь {user.username} ушел")

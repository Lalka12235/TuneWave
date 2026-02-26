from app.infrastructure.ws.connection_manager import manager
import json


class NotifyService:

    async def send_mesasge_for_user(
        self,
        data_message: dict[str,str]
    ) -> None:
        user_id = data_message['user_id']
        await manager.send_personal_message(
            json.dumps(data_message), user_id
        )

    async def send_message_for_requester(self,data_message: dict[str,str]):
        requester_id = data_message['requester_id']
        await manager.send_personal_message(
            json.dumps(data_message), requester_id
        )
        
    async def send_message_for_accepter(self,data_message: dict[str,str]):
        accepter_id = data_message['accepter_id']
        await manager.send_personal_message(
            json.dumps(data_message), accepter_id
        )
    
    

    async def send_message_for_room(
        self,
        data_message: dict[str,str]
    ) -> None:
        await manager.broadcast(data_message['room_id'] if data_message['room_id'] else manager.GLOBAL_ROOM_ID, json.dumps(data_message))
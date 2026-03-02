from typing import Any
import uuid
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.exceptions.room_exception import RoomNotFoundError

class RoomQueueService:

    def __init__(
        self,
        room_repo: RoomGateway,
    ):
        self.room_repo = room_repo

    async def get_room_queue(self,room_id: uuid.UUID) -> list[dict[str,Any]]:
        """
        Получает текущую очередь треков для комнаты.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        queue_response = []
        if not room.room_track:
            return queue_response

        for assoc in room.room_track:
            if assoc.track:
                res = {
                    'track': assoc.track,
                    'order_inde_queue': assoc.order_in_queue,
                    'id': assoc.id,
                    'added_at': assoc.added_at
                }
                queue_response.append(res)
        
        return queue_response
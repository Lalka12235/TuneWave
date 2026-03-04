import uuid

from app.domain.entity import UserEntity,RoomTrackAssociationEntity
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.room_track_association_gateway import RoomTrackAssociationGateway


from app.domain.interfaces.track_gateway import TrackGateway

from app.infrastructure.ws.manager_notify_service import NotifyService
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway

from app.domain.exceptions.room_exception import RoomNotFoundError,RoomPermissionDeniedError
from app.domain.exceptions.exception import ServerError

class RoomQueueService:
    def __init__(
        self,
        room_repo: RoomGateway,
        room_track_repo: RoomTrackAssociationGateway,
        track_repo: TrackGateway,
        member_room_repo: MemberRoomAssociationGateway,
        notify_service: NotifyService
    ):
        self.room_repo = room_repo
        self.room_track_repo = room_track_repo
        self.track_repo = track_repo
        self.member_room_repo = member_room_repo
        self.notify_service = notify_service

    #todo
    #def _reorder_queue(self,room_id: uuid.UUID):
    #    """
    #    Переупорядочивает order_in_queue для всех оставшихся треков в очереди.
    #    """
    #    queue_association = self.self._db.query(RoomTrackAssociationModel).where(
    #        RoomTrackAssociationModel.room_id == room_id,
    #    ).order_by(RoomTrackAssociationModel.order_in_queue).all()
#
    #    try:
    #        for index,assoc in enumerate(queue_association):
    #            assoc.order_in_queue = index
    #            self.self._db.add(assoc)
#
    #        
    #    except Exception as e:
    #        
    #        raise HTTPException(
    #            status_code=500,
    #            detail=f'Не удалось перепорядочить очередь.{e}'
    #        )


    async def move_track_in_queue(self,room_id: uuid.UUID,association_id: uuid.UUID,current_user: UserEntity,new_position: int,) -> RoomTrackAssociationEntity:
        """Перемещает трек в очереди."""
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        if room.owner_id != current_user.id:
            raise  RoomPermissionDeniedError()
        
        queue = self.room_track_repo.get_queue_for_room(room_id)
        if not queue:
            raise ValueError("Очередь комнаты пуста.")
        
        track_to_move = None
        for assoc in queue:
            if assoc.id == association_id:
                track_to_move = assoc
                break
        
        current_length = len(queue)
        if not track_to_move:
            raise ValueError(f"Трек с ассоциацией ID {association_id} не найден в очереди.")
        
        if not (0 <= new_position < current_length):
            raise ValueError(f"Некорректная позиция: {new_position}. Допустимый диапазон от 0 до {current_length - 1}.")
    
        try:
            queue.remove(track_to_move)

            queue.insert(new_position, track_to_move)

            for index, assoc in enumerate(queue):
                assoc.order_in_queue = index
        except Exception as e:
            raise ServerError(
                detail=f'Не удалось перепорядочить очередь.{e}'
            )

        try:
            updated_queue = self.room_track_repo.get_queue_for_room( room_id)
            update_message = {
                "action": "move",
                "queue": [
                    {
                        "id": str(assoc.id),
                        "track_id": str(assoc.track_id),
                        "order": assoc.order_in_queue,
                        "title": assoc.track.title,
                        "artist": assoc.track.artist_names,
                        "album_art_url": assoc.track.album_name
                    } for assoc in updated_queue
                ]
            }
            await self.notify_service.send_message_for_room(update_message)
        except Exception as e:
            print(f"Ошибка при отправке WebSocket-сообщения: {e}")

        return {"message": "Трек успешно перемещён."}
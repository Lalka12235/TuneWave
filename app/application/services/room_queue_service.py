import json
import uuid

from app.domain.entity import UserEntity,RoomTrackAssociationEntity
from app.domain.interfaces.room_repo import RoomRepository
from app.domain.interfaces.room_track_association_repo import RoomTrackAssociationRepository

from app.domain.enum import Role
from app.presentation.schemas.room_schemas import TrackInQueueResponse

from app.application.mappers.mappers import TrackMapper
from app.domain.interfaces.track_repo import TrackRepository

from app.infrastructure.ws.connection_manager import manager
from app.domain.interfaces.member_room_association import MemberRoomAssociationRepository

from app.domain.exceptions.room_exception import RoomNotFoundError,UserNotInRoomError,RoomPermissionDeniedError,TrackAlreadyInQueueError
from app.domain.exceptions.track_exception import TrackNotFound
from app.domain.exceptions.exception import ServerError

class RoomQueueService:
    """
    Реализует бизнес логику для работы с очередью треков комнаты
    """
    
    def __init__(
        self,
        room_repo: RoomRepository,
        room_track_repo: RoomTrackAssociationRepository,
        track_repo: TrackRepository,
        member_room_repo: MemberRoomAssociationRepository,
    ):
        self.room_repo = room_repo
        self.room_track_repo = room_track_repo
        self.track_repo = track_repo
        self.member_room_repo = member_room_repo
    
    
    async def get_room_queue(self,room_id: uuid.UUID) -> list[TrackInQueueResponse]:
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
                res = TrackInQueueResponse(
                    track=TrackMapper.to_response_track(assoc.track),
                    order_in_queue=assoc.order_in_queue,
                    id=assoc.id,
                    added_at=assoc.added_at
                )
                queue_response.append(res)
        

        return queue_response
    
    async def add_track_to_queue(
    self, 
    room_id: uuid.UUID,
    track_spotify_id: str, 
    current_user: UserEntity,
        ) -> RoomTrackAssociationEntity:
        """
        Добавляет трек в очередь конкретной комнаты.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        user_assoc = self.member_room_repo.get_association_by_ids(current_user.id,room_id)

        if not user_assoc:
            raise UserNotInRoomError()

        is_owner = (room.owner_id == current_user.id)
        is_moderator = (user_assoc and user_assoc.role == Role.MODERATOR.value)

        if not is_owner and not is_moderator:
            raise RoomPermissionDeniedError(detail="У вас недостаточно прав.")
        
        track = self.track_repo.get_track_by_spotify_id(track_spotify_id)
        if not track:
            raise TrackNotFound()
        
        dublicate_in_queue = self.room_track_repo.get_association_by_room_and_track(room_id,track.id)
        if dublicate_in_queue:
            raise TrackAlreadyInQueueError()
        
        order_in_queue = self.room_track_repo.get_last_order_in_queue(room_id)

        try:
            add_track = self.room_track_repo.add_track_to_queue(room_id,track.id,order_in_queue,current_user.id)
        except Exception as e:
            raise ServerError(
                detail=f"Не удалось добавить трек в очередь{e}."
            )
        try:
            updated_queue = self.room_track_repo.get_queue_for_room( room_id)
            update_message = {
                "action": "add",
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
            await manager.broadcast(room_id, json.dumps(update_message))
        except Exception as e:
            print(f"Ошибка при отправке WebSocket-сообщения: {e}")


        return add_track
    

    async def remove_track_from_queue(
        self,
        room_id: uuid.UUID,
        association_id: uuid.UUID,
        current_user_id: uuid.UUID,
) -> dict[str,str]:
        """
        Удаляет конкретный трек из очереди комнаты по ID ассоциации.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        
        user_assoc = self.member_room_repo.get_association_by_ids(current_user_id,room_id)

        if not user_assoc:
            raise UserNotInRoomError()

        is_owner = (room.owner_id == current_user_id)
        is_moderator = (user_assoc and user_assoc.role == Role.MODERATOR.value)

        if not is_owner and not is_moderator:
            raise RoomPermissionDeniedError(detail="У вас недостаточно прав.")

        
        self.db_association = self.room_track_repo.get_association_by_id(association_id)
        if not self.db_association or str(self.db_association.room_id) != str(room_id):
            raise ValueError("Ассоциация не найдена или не принадлежит этой комнате.")
        
        try:
            deleted_successfully = self.room_track_repo.remove_track_from_queue_by_association_id(
                association_id
            )
            if deleted_successfully:
                self._reorder_queue(room_id)
                
        except Exception as e:
            raise ServerError(
                detail=f"Не удалось удалить трек из очередь{e}."
            )
        try:
            updated_queue = self.room_track_repo.get_queue_for_room( room_id)
            update_message = {
                "action": "remove",
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
            await manager.broadcast(room_id, json.dumps(update_message))
        except Exception as e:
            print(f"Ошибка при отправке WebSocket-сообщения: {e}")

        return {
            'status': 'success',
            'detail': 'remove track from queue',
            'response': deleted_successfully
        }
    

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
            await manager.broadcast(room_id, json.dumps(update_message))
        except Exception as e:
            print(f"Ошибка при отправке WebSocket-сообщения: {e}")

        return {"message": "Трек успешно перемещён."}
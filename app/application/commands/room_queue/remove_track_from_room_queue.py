import uuid

from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.room_track_association_gateway import RoomTrackAssociationGateway

from app.domain.enum import Role

from app.domain.interfaces.track_gateway import TrackGateway

from app.infrastructure.ws.manager_notify_service import NotifyService
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway

from app.domain.exceptions.room_exception import RoomNotFoundError,UserNotInRoomError,RoomPermissionDeniedError
from app.domain.exceptions.exception import ServerError

class RemoveTrackFromQueue:
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

        if not is_owner or not is_moderator:
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
            
            updated_queue = self.room_track_repo.get_queue_for_room( room_id)
            await self.notify_service.send_message_for_room(
            {
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
        )
            return {
            'status': 'success',
            'detail': 'remove track from queue',
            'response': deleted_successfully
        }       
        except Exception as e:
            raise ServerError(
                detail=f"Не удалось удалить трек из очередь{e}."
            )
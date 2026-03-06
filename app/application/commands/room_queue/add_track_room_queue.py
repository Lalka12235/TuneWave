import uuid

from app.domain.entity import UserEntity,RoomTrackAssociationEntity
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.room_track_association_gateway import RoomTrackAssociationGateway

from app.domain.enum import Role

from app.domain.interfaces.track_gateway import TrackGateway

from app.infrastructure.ws.manager_notify_service import NotifyService
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway

from app.domain.exceptions.room_exception import RoomNotFoundError,UserNotInRoomError,RoomPermissionDeniedError,TrackAlreadyInQueueError
from app.domain.exceptions.track_exception import TrackNotFound
from app.domain.exceptions.exception import ServerError

class AddTrackRoomQueue:
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

        if not is_owner or not is_moderator:
            raise RoomPermissionDeniedError(detail="У вас недостаточно прав.")
        
        #todo
        track = self.track_repo.get_track_by_spotify_id(track_spotify_id)
        if not track:
            raise TrackNotFound()
        
        dublicate_in_queue = self.room_track_repo.get_association_by_room_and_track(room_id,track.id)
        if dublicate_in_queue:
            raise TrackAlreadyInQueueError()
        
        order_in_queue = self.room_track_repo.get_last_order_in_queue(room_id)

        try:
            add_track = self.room_track_repo.add_track_to_queue(room_id,track.id,order_in_queue,current_user.id)
            updated_queue = self.room_track_repo.get_queue_for_room( room_id)
            await self.notify_service.send_message_for_room(
            {
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
            )
            return add_track
        except Exception as e:
            raise ServerError(
                detail=f"Не удалось добавить трек в очередь{e}."
            )
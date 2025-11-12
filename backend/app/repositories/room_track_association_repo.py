from sqlalchemy import select,delete,func
from sqlalchemy.orm import Session,joinedload
from app.models.room_track_association import RoomTrackAssociationModel
import uuid
from app.schemas.entity import RoomTrackAssociationEntity
from app.repositories.abc.room_track_association_repo import RoomTrackAssociationRepository



class SQLalchemyRoomTrackAssociationRepository(RoomTrackAssociationRepository):

    def __init__(self, db: Session):
        self._db = db

    
    def from_model_to_entity(self,model: RoomTrackAssociationModel) -> RoomTrackAssociationEntity:
        return RoomTrackAssociationEntity(
            id=model.id,
            room_id=model.room_id,
            track_id=model.track_id,
            order_in_queue=model.order_in_queue,
            added_at=model.added_at,
            added_by_user_id=model.added_by_user_id
        )

    
    def add_track_to_queue(
        self,
        room_id: uuid.UUID,
        track_id: uuid.UUID,
        order_in_queue: int,
        user_id: uuid.UUID,
) -> RoomTrackAssociationEntity:
        """Добавляет новый трек в очередь конкретной комнаты."""
        new_room_track = RoomTrackAssociationModel(
            room_id=room_id,
            track_id=track_id,
            order_in_queue=order_in_queue,
            added_by_user_id=user_id,
        )
        self._db.add(new_room_track)
        self._db.flush()
        self._db.refresh(new_room_track)
        return self.from_model_to_entity(new_room_track)
    

    
    def get_queue_for_room(self,room_id: uuid.UUID) -> list[RoomTrackAssociationEntity]:
        """Получает все треки, находящиеся в очереди данной комнаты, отсортированные по порядку."""
        stmt = select(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
        ).order_by(RoomTrackAssociationModel.order_in_queue).options(
                joinedload(RoomTrackAssociationModel.track),
                joinedload(RoomTrackAssociationModel.user)
            )
        result = self._db.execute(stmt).scalars().all()
        return result
    

    
    def remove_track_from_queue(self,room_id: uuid.UUID,track_id: uuid.UUID) -> bool:
        """Удаляет конкретный трек из очереди комнаты по room_id и track_id."""
        stmt = delete(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
            RoomTrackAssociationModel.track_id == track_id,
        )
        result = self._db.execute(stmt)
        return result.rowcount > 0
    

    
    def get_last_order_in_queue(self,room_id: uuid.UUID) -> int:
        """Определяет следующий доступный номер для нового трека в очереди."""
        stmt = select(func.max(RoomTrackAssociationModel.order_in_queue)).where(
            RoomTrackAssociationModel.room_id == room_id
        )
        max_order = self._db.execute(stmt).scalar_one_or_none()
        return (max_order if max_order is not None else -1) + 1
    

    
    def get_association_by_id(self, association_id: uuid.UUID) -> RoomTrackAssociationEntity | None:
        """Получает ассоциацию трека с комнатой по её ID."""
        stmt = select(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.id == association_id
        ).options(
                joinedload(RoomTrackAssociationModel.track),
                joinedload(RoomTrackAssociationModel.user)
            )
        result = self._db.execute(stmt).scalars().first()
        return self.from_model_to_entity(result)


    
    def remove_track_from_queue_by_association_id(self, association_id: uuid.UUID) -> bool:
        """Удаляет трек из очереди по ID ассоциации."""
        stmt = delete(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.id == association_id
        )
        result = self._db.execute(stmt)
        return result.rowcount > 0
    

    
    def get_association_by_room_and_track(self, room_id: uuid.UUID,track_id: uuid.UUID) -> RoomTrackAssociationEntity | None:
        """Получает ассоциацию трека с комнатой по её ID."""
        stmt = select(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
            RoomTrackAssociationModel.track_id == track_id,
        ).options(
                joinedload(RoomTrackAssociationModel.track),
                joinedload(RoomTrackAssociationModel.user)
            )
        result = self._db.execute(stmt).scalars().first()
        return self.from_model_to_entity(result)
    

    
    def get_first_track_in_queue(self,room_id: uuid.UUID) -> RoomTrackAssociationEntity | None:
        """_summary_

        Args:
            room_id (uuid.UUID): _description_

        Returns:
            RoomTrackAssociationModel: _description_
        """
        stmt = select(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
        ).order_by(RoomTrackAssociationModel.order_in_queue.asc()).options(
                joinedload(RoomTrackAssociationModel.track),
                joinedload(RoomTrackAssociationModel.user)
            ).limit(1)
        result = self._db.execute(stmt).scalars().first()
        return self.from_model_to_entity(result)
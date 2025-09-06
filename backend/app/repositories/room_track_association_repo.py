from sqlalchemy import select,delete,func
from sqlalchemy.orm import Session,joinedload
from app.models import RoomTrackAssociationModel
import uuid



class RoomTrackAssociationRepository:

    @staticmethod
    def add_track_to_queue(
        db: Session,
        room_id: uuid.UUID,
        track_id: uuid.UUID,
        order_in_queue: int,
        user_id: uuid.UUID,
) -> RoomTrackAssociationModel:
        """Добавляет новый трек в очередь конкретной комнаты."""
        new_room_track = RoomTrackAssociationModel(
            room_id=room_id,
            track_id=track_id,
            order_in_queue=order_in_queue,
            added_by_user_id=user_id,
        )
        db.add(new_room_track)
        db.flush()
        return new_room_track
    

    @staticmethod
    def get_queue_for_room(db: Session,room_id: uuid.UUID) -> list[RoomTrackAssociationModel]:
        """Получает все треки, находящиеся в очереди данной комнаты, отсортированные по порядку."""
        stmt = select(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
        ).order_by(RoomTrackAssociationModel.order_in_queue).options(
                joinedload(RoomTrackAssociationModel.track),
                joinedload(RoomTrackAssociationModel.user)
            )
        return db.execute(stmt).scalars().all()
    

    @staticmethod
    def remove_track_from_queue(db: Session,room_id: uuid.UUID,track_id: uuid.UUID) -> bool:
        """Удаляет конкретный трек из очереди комнаты по room_id и track_id."""
        stmt = delete(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
            RoomTrackAssociationModel.track_id == track_id,
        )
        result = db.execute(stmt)
        return result.rowcount > 0
    

    @staticmethod
    def get_last_order_in_queue(db: Session,room_id: uuid.UUID) -> int:
        """Определяет следующий доступный номер для нового трека в очереди."""
        stmt = select(func.max(RoomTrackAssociationModel.order_in_queue)).where(
            RoomTrackAssociationModel.room_id == room_id
        )
        max_order = db.execute(stmt).scalar_one_or_none()
        return (max_order if max_order is not None else -1) + 1
    

    @staticmethod
    def get_association_by_id(db: Session, association_id: uuid.UUID) -> RoomTrackAssociationModel | None:
        """Получает ассоциацию трека с комнатой по её ID."""
        stmt = select(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.id == association_id
        ).options(
                joinedload(RoomTrackAssociationModel.track),
                joinedload(RoomTrackAssociationModel.user)
            )
        return db.execute(stmt).scalars().first()


    @staticmethod
    def remove_track_from_queue_by_association_id(db: Session, association_id: uuid.UUID) -> bool:
        """Удаляет трек из очереди по ID ассоциации."""
        stmt = delete(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.id == association_id
        )
        result = db.execute(stmt)
        return result.rowcount > 0
    

    @staticmethod
    def get_association_by_room_and_track(db: Session, room_id: uuid.UUID,track_id: uuid.UUID) -> RoomTrackAssociationModel | None:
        """Получает ассоциацию трека с комнатой по её ID."""
        stmt = select(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
            RoomTrackAssociationModel.track_id == track_id,
        ).options(
                joinedload(RoomTrackAssociationModel.track),
                joinedload(RoomTrackAssociationModel.user)
            )
        return db.execute(stmt).scalars().first()
    

    @staticmethod
    def get_first_track_in_queue(db: Session,room_id: uuid.UUID) -> RoomTrackAssociationModel | None:
        """_summary_

        Args:
            db (Session): _description_
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
        return db.execute(stmt).scalars().first()
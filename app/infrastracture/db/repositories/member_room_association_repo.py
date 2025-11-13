from sqlalchemy import select,delete,update,and_
from sqlalchemy.orm import Session,joinedload
from app.infrastracture.db.models import Member_room_association,Room
from app.domain.entity import RoomEntity,MemberRoomEntity
import uuid
from app.domain.interfaces.member_room_association import MemberRoomAssociationRepository


class SQLalchemyMemberRoomAssociationRepository(MemberRoomAssociationRepository):
    """
    Репозиторий для выполнения операций CRUD над моделью Member_room_association.
    Отвечает за управление связями между пользователями и комнатами (членство).
    """

    def __init__(self, db: Session):
        self._db = db
    

    def from_model_to_entity(self,model: Member_room_association | Room) -> MemberRoomEntity | RoomEntity:
        if isinstance(model,Member_room_association):
            return MemberRoomEntity(
                user_id=model.user_id,
                room_id=model.user_id,
                role=model.role,
                joined_at=model.joined_at,
            )
        else:
            return RoomEntity(
                id=model.id,
                name=model.name,
                max_members=model.max_members,
                owner_id=model.owner_id,
                is_private=model.is_private,
                password_hash=model.password_hash,
                current_track_id=model.current_track_id,
                current_track_position_ms=model.current_track_position_ms,
                is_playing=model.is_playing,
                created_at=model.created_at,
                playback_host_id=model.playback_host_id,
                active_spotify_device_id=model.active_spotify_device_id,
                current_playing_track_association_id=model.current_playing_track_association_id
        )
    


    
    def add_member(self,user_id: uuid.UUID,room_id: uuid.UUID,role: str) -> MemberRoomEntity:
        """
        Добавляет пользователя в комнату (создает запись о членстве).
        
        Args:
            user_id (uuid.UUID): ID пользователя, который присоединяется.
            room_id (uuid.UUID): ID комнаты, к которой присоединяется пользователь.
            
        Returns:
            Member_room_association: Созданный объект ассоциации.
        """
        new_member_room = Member_room_association(
            user_id=user_id,
            room_id=room_id,
            role=role,
        )
        self._db.add(new_member_room)
        self._db.flush()
        self._db.refresh(new_member_room)
        return self.from_model_to_entity(new_member_room)
    

    
    def remove_member(self,user_id: uuid.UUID, room_id: uuid.UUID) -> bool:
        """
        Удаляет пользователя из комнаты (удаляет запись о членстве).
        
        Args:
            user_id (uuid.UUID): ID пользователя, которого нужно удалить.
            room_id (uuid.UUID): ID комнаты, из которой нужно удалить пользователя.
            
        Returns:
            bool: True, если членство было успешно удалено, иначе False.
        """
        stmt = delete(Member_room_association).where(
            Member_room_association.room_id==room_id,
            Member_room_association.user_id==user_id,
        )
        result = self._db.execute(stmt)
        return result.rowcount > 0
    

    
    def get_association_by_ids(self, user_id: uuid.UUID, room_id: uuid.UUID) -> MemberRoomEntity | None:
        """
        Получает запись об ассоциации (членстве) по ID пользователя и ID комнаты.
        
        Args:
            user_id (uuid.UUID): ID пользователя.
            room_id (uuid.UUID): ID комнаты.
            
        Returns:
            Member_room_association | None: Объект ассоциации, если найден, иначе None.
        """

        stmt = select(Member_room_association).where(
            Member_room_association.room_id==room_id,
            Member_room_association.user_id==user_id,
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return self.from_model_to_entity(result)
    

    
    def get_members_by_room_id(self, room_id: uuid.UUID) -> list[MemberRoomEntity]:
        """
        Получает список объектов User, которые являются участниками данной комнаты.
        
        Args:
            room_id (uuid.UUID): ID комнаты.
            
        Returns:
            List[User]: Список объектов User, являющихся участниками комнаты.
        """
        stmt = select(Member_room_association).where(
            Member_room_association.room_id == room_id,
        ).options(
            joinedload(Member_room_association.user)
        )
        result = self._db.execute(stmt).scalars().all()
        return result
    

    
    def get_rooms_by_user_id(self, user_id: uuid.UUID) -> list[RoomEntity]:
        """
        Получает список комнат пользователя

        Args:
            user_id (uuid.UUID): _description_

        Returns:
            list[RoomEntity]: _description_
        """
        stmt = select(Room).join(
            Member_room_association
        ).where(
            Member_room_association.user_id == user_id
        ).options(
            joinedload(Room.owner),
            joinedload(Room.member_room),
            joinedload(Room.current_track)
        )
        result = self._db.execute(stmt).scalars().unique().all()
        return result
    

    
    def update_role(self,room_id: uuid.UUID,user_id: uuid.UUID,role: str) -> MemberRoomEntity | None:
        """
        Обновляет роль члена комнаты в базе данных.
        
        Args:
            room_id (uuid.UUID): ID комнаты, в которой нужно обновить роль.
            user_id (uuid.UUID): ID пользователя, чью роль нужно обновить.
            role (str): Новая роль для пользователя.
            
        Returns:
            Member_room_association | None: Обновленный объект ассоциации, если найден и обновлен, иначе None.
        """
        stmt = update(Member_room_association).where(
                Member_room_association.user_id == user_id,
                Member_room_association.room_id == room_id,
            ).values(role=role).returning(Member_room_association)
        result = self._db.execute(stmt).scalar_one_or_none()
        return self.from_model_to_entity(result)
    

    
    def get_member_room_association(self, room_id: uuid.UUID, user_id: uuid.UUID) -> MemberRoomEntity | None:
        """
        Получает запись об участии пользователя в конкретной комнате.
        Загружает отношения user и room.

        Args:
            room_id (uuid.UUID): ID комнаты.
            user_id (uuid.UUID): ID пользователя.

        Returns:
            Optional[Member_room_association]: Объект ассоциации, если найден, иначе None.
        """
        
        stmt = select(Member_room_association).options(
           joinedload(Member_room_association.user),
           joinedload(Member_room_association.room)
        ).where(
           and_(
               Member_room_association.room_id == room_id,
               Member_room_association.user_id == user_id
           )
        )
        result = self._db.execute(stmt).scalars().first()
        return self.from_model_to_entity(result)
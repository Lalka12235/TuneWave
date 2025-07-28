from fastapi import HTTPException,status
from app.repositories.room_repo import RoomRepository
from app.repositories.member_room_association_repo import MemberRoomAssociationRepository
from sqlalchemy.orm import Session
from app.schemas.room_schemas import RoomResponse, RoomCreate, RoomUpdate
from app.schemas.user_schemas import UserResponse
from app.models.room import Room
import uuid
from typing import Any
from app.utils.hash import make_hash_pass,verify_pass
from app.models.user import User


class RoomService:

    @staticmethod
    def _map_room_to_response(room: Room) -> RoomResponse:
        """
        Вспомогательный метод для преобразования объекта User SQLAlchemy в Pydantic UserResponse.
        Это централизованное место для форматирования данных, возвращаемых клиенту.
        """
        # Pydantic's model_validate() автоматически преобразует SQLAlchemy ORM-объект
        # в Pydantic-модель, благодаря Config.from_attributes = True в UserResponse.
        return RoomResponse.model_validate(room)
    
    @staticmethod
    def _map_user_to_response(user: User) -> UserResponse:
        """
        Вспомогательный метод для преобразования объекта User SQLAlchemy в Pydantic UserResponse.
        """
        return UserResponse.model_validate(user)
    

    @staticmethod
    def get_room_by_id(db: Session,room_id: uuid.UUID) -> dict[str,Any]:
        """
        Получает комнату по ее уникальному ID.
        """
        room = RoomRepository.get_room_by_id(db,room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail='Room not found'
            )
        
        return RoomService._map_room_to_response(room)
    

    @staticmethod
    def get_room_by_name(db: Session,name: str) -> RoomResponse:
        """
        Получает комнату по ее названию.
        """
        room = RoomRepository.get_room_by_name(db,name)
        if not room:
            raise HTTPException(
                status_code=404,
                detail='Room not found'
            )
        
        return RoomService._map_room_to_response(room) 
    

    @staticmethod
    def get_all_rooms(db: Session) -> list[RoomResponse]:
        """
        Получает список всех комнат из базы данных.
        """
        rooms_list = RoomRepository.get_all_rooms(db)
        
        return [RoomService._map_room_to_response(room) for room in rooms_list]
    

    @staticmethod
    def create_room(db: Session,room_data: RoomCreate,owner: User) -> RoomResponse:
        """
        Создает новую комнату.
        Включает проверку уникальности имени и хэширование пароля.
        """

        room = RoomRepository.get_room_by_name(db,room_data.name)
        if room:
            raise HTTPException(
                status_code=404,
                detail=f"Комната с названием '{room_data.name}' уже существует."
            )
        
        room_data_dict = room_data.model_dump()
        room_data_dict['owner_id'] = owner.id
        
        if room_data.is_private:
            if not room_data.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Для приватной комнаты требуется пароль."
                )
            room_data_dict['password'] = make_hash_pass(room_data.password)
        room_data_dict['password_hash'] = None
        if room_data.password:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль не может быть установлен для не приватной комнаты."
            )
        
        room_data_dict.pop('password', None)
        new_room = RoomRepository.create_room(db,room_data_dict)
        db.commit()
        db.refresh(new_room)
        return RoomService._map_room_to_response(new_room)
    

    @staticmethod
    def update_room(db: Session, room_id: uuid.UUID, update_data: RoomUpdate, current_user: User) -> RoomResponse:
        """
        Обновляет существующую комнату.
        Только владелец комнаты может ее обновить.
        """
        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Комната не найдена."
            )
        
        if room.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для обновления этой комнаты."
            )
        
        data_to_update = update_data.model_dump(exclude_unset=True)

        if 'is_private' in data_to_update:
            if data_to_update['is_private'] and 'password' not in data_to_update:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Для установки приватности комнаты требуется новый пароль."
                )
            elif not data_to_update['is_private'] and 'password' in data_to_update and data_to_update['password'] is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пароль не может быть установлен для не приватной комнаты."
                )
        
        if 'password' in data_to_update and data_to_update['password'] is not None:
            data_to_update['password_hash'] = make_hash_pass(data_to_update.pop('password'))
        elif 'password' in data_to_update and data_to_update['password'] is None:
            data_to_update['password_hash'] = None
        
        updated_room_db = RoomRepository.update_room(db, room, data_to_update)
        
        db.commit()
        db.refresh(updated_room_db)

        return RoomService._map_room_to_response(updated_room_db)
    

    @staticmethod
    def delete_room(db: Session,room_id: uuid.UUID,owner: User) -> dict[str,Any]:
        """_summary_

        Args:
            db (Session): _description_
            room_id (uuid.UUID): _description_
            owner (User): _description_

        Returns:
            dict[str,Any]: _description_
        """

        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Комната не найдена."
            )
        
        if room.owner_id != owner.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для обновления этой комнаты."
            )
        
        deleted_successfully = RoomRepository.delete_room(db,room_id)

        db.commit()

        if deleted_successfully:
            return {
                'status': 'success',
                'detail': 'Комната успешно удалена.',
                'id': str(room_id),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось удалить комнату."
            )
        
    
    @staticmethod
    def verify_room_password(room: Room, password: str) -> bool:
        """
        Проверяет предоставленный пароль для приватной комнаты.
        """
        if not room.is_private or not room.password_hash:
            return False 

        return verify_pass(password, room.password_hash)
    
    @staticmethod
    def join_room(db: Session,user: User,room_id: uuid.UUID,password: str | None = None) -> RoomResponse:
        """
        Пользователь присоединяется к комнате.
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты, к которой присоединяется пользователь.
            user (User): Объект текущего пользователя.
            password (Optional[str]): Пароль для приватной комнаты.
            
        Returns:
            RoomResponse: Объект комнаты, к которой присоединился пользователь.
            
        Raises:
            HTTPException: Если комната не найдена, пользователь уже является участником,
                           неверный пароль, или комната переполнена.
        """
        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Комната не найдена."
            )
        
        existing_association = MemberRoomAssociationRepository.get_association_by_ids(db, user.id, room_id)
        if existing_association:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Вы уже являетесь участником этой комнаты."
            )
        
        if room.is_private:
            if not password or not RoomService.verify_room_password(room, password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный пароль для приватной комнаты."
                )
            
        current_members_count = len(MemberRoomAssociationRepository.get_members_by_room_id(db, room_id))
        if current_members_count >= room.max_members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Комната заполнена. Невозможно присоединиться."
            )
        
        new_association = MemberRoomAssociationRepository.add_member(db,user.id,room_id)

        db.commit()
        db.refresh(new_association)

        return RoomService._map_room_to_response(room)

    @staticmethod
    def leave_room(db: Session, room_id: uuid.UUID, user: User) -> dict[str, Any]:
        """
        Пользователь покидает комнату.
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты, которую покидает пользователь.
            user (User): Объект текущего пользователя.
            
        Returns:
            dict[str, Any]: Сообщение об успешном выходе.
            
        Raises:
            HTTPException: Если пользователь не является участником комнаты.
        """
        existing_association = MemberRoomAssociationRepository.get_association_by_ids(db, user.id, room_id)
        if not existing_association:
            raise HTTPException(
                status_code=status.HTTP_404_CONFLICT,
                detail="Вы не являетесь участником этой комнаты."
            )
        
        deleted_successfully = MemberRoomAssociationRepository.remove_member(db,user.id,room_id)

        db.commit()

        if deleted_successfully:
            return {
                'status': 'success',
                'detail': f"Вы успешно покинули комнату с ID: {room_id}.",
                'user_id': str(user.id),
                'room_id': str(room_id)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось покинуть комнату."
            )
        
    
    @staticmethod
    def get_room_members(db: Session,room_id: uuid.UUID) -> list[UserResponse]:
        """
        Получает список участников комнаты.
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты.
            
        Returns:
            List[UserResponse]: Список объектов UserResponse, являющихся участниками комнаты.
            
        Raises:
            HTTPException: Если комната не найдена.
        """
        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Комната не найдена."
            )
        
        members = MemberRoomAssociationRepository.get_members_by_room_id(db,room_id)
        
        return [RoomService._map_user_to_response(member) for member in members]
    

    @staticmethod
    def get_user_rooms(db: Session,user: User) -> list[RoomResponse]:
        """
        Получает список всех комнат, в которых состоит данный пользователь.
        
        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user (User): Объект текущего пользователя.
            
        Returns:
            List[RoomResponse]: Список объектов RoomResponse, в которых состоит пользователь.
        """
        rooms = MemberRoomAssociationRepository.get_rooms_by_user_id(db,user.id)
        return [RoomService._map_room_to_response(room) for room in rooms]
    

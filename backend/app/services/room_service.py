import uuid
from typing import Any

from fastapi import HTTPException, status

from app.logger.log_config import logger
from app.models import User
from app.repositories.member_room_association_repo import (
    MemberRoomAssociationRepository,
)
from app.repositories.room_repo import RoomRepository

from app.schemas.enum import Role
from app.schemas.room_schemas import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)

from app.auth.hash import make_hash_pass
from app.ws.connection_manager import manager
from app.services.mapper import RoomMapper


class RoomService:

    def __init__(
            self,
            room_repo: RoomRepository,
            member_room_repo: MemberRoomAssociationRepository,
        ):
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo

    
    async def get_room_by_id(self,room_id: uuid.UUID) -> dict[str,Any]:
        """
        Получает комнату по ее уникальному ID.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail='Room not found'
            )
        
        return RoomMapper.to_response(room)
    

    
    async def get_room_by_name(self,name: str) -> RoomResponse:
        """
        Получает комнату по ее названию.
        """
        room = self.room_repo.get_room_by_name(name)
        if not room:
            raise HTTPException(
                status_code=404,
                detail='Room not found'
            )
        
        return RoomMapper.to_response(room) 
    

    
    async def get_all_rooms(self) -> list[RoomResponse]:
        """
        Получает список всех комнат из базы данных.
        """
        rooms_list = self.room_repo.get_all_rooms()
        
        return [RoomMapper.to_response(room) for room in rooms_list]
    

    
    async def create_room(self,room_data: RoomCreate,owner: User) -> RoomResponse:
        """
        Создает новую комнату.
        Включает проверку уникальности имени и хэширование пароля.
        """

        room = self.room_repo.get_room_by_name(room_data.name)
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
        try:
            new_room = self.room_repo.create_room(room_data_dict)
            
            self.member_room_repo.add_member(
                owner.id,
                new_room.id,
                role=Role.OWNER.value
            )

            room_response = RoomMapper.to_response(new_room)
            websocket_message = {
            "action": "room_created",
            "room_data": room_response.model_dump_json()
            }
            await manager.broadcast(manager.GLOBAL_ROOM_ID,websocket_message)

            return RoomMapper.to_response(new_room)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании комнаты: {e}"
            )
    

    
    def update_room(self, room_id: uuid.UUID, update_data: RoomUpdate, current_user: User) -> RoomResponse:
        """
        Обновляет существующую комнату.
        Только владелец комнаты может ее обновить.
        """
        room = self.room_repo.get_room_by_id(room_id)
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
        
        try:
            updated_room_db = self.room_repo.update_room(room, data_to_update)

            return RoomMapper.to_response(updated_room_db)
        except Exception as e:
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при обновлении комнаты: {e}"
            )
    

    
    def delete_room(self,room_id: uuid.UUID,owner: User) -> dict[str,Any]:
        """_summary_

        Args:
            self.db (Session): _description_
            room_id (uuid.UUID): _description_
            owner (User): _description_

        Returns:
            dict[str,Any]: _description_
        """

        room = self.room_repo.get_room_by_id(room_id)
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
        try:
            deleted_successfully = self.room_repo.delete_room(room_id)

            if deleted_successfully:
                return {
                    'status': 'success',
                    'detail': 'Комната успешно удалена.',
                    'id': str(room_id),
                }
        except Exception as e:
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось удалить комнату. {e}"
            )
        
    
    async def get_user_rooms(self,user: User) -> list[RoomResponse]:
        """
        Получает список всех комнат, в которых состоит данный пользователь.
        
        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
            user (User): Объект текущего пользователя.
            
        Returns:
            List[RoomResponse]: Список объектов RoomResponse, в которых состоит пользователь.
        """
        rooms = self.member_room_repo.get_rooms_by_user_id(user.id)
        return [RoomMapper.to_response(room) for room in rooms]
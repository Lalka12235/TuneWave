from fastapi import HTTPException,status
from app.repositories.room_repo import RoomRepository
from app.repositories.member_room_association_repo import MemberRoomAssociationRepository
from app.schemas.room_member_schemas import RoomMemberResponse
from app.models.member_room_association import Member_room_association
from sqlalchemy.orm import Session
from app.schemas.room_schemas import RoomResponse, RoomCreate, RoomUpdate,TrackInQueueResponse
from app.schemas.user_schemas import UserResponse
from app.services.user_service import UserService
from app.models.room import Room
from app.services.track_service import TrackService
from app.services.spotify_sevice import SpotifyService
import uuid
from typing import Any
from app.utils.hash import make_hash_pass,verify_pass
from app.models.user import User
from app.models.room_track_association import RoomTrackAssociationModel
from app.repositories.room_track_association_repo import RoomTrackAssociationRepository
from app.exceptions.exception import (
    TrackNotFoundException, 
    TrackAlreadyInQueueException, 
    RoomNotFoundException,
    UnauthorizedRoomActionException
)
from app.ws.connection_manager import manager,GLOBAL_ROOM_ID
import json
from app.schemas.enum import ControlAction,Role,NotificationType
from app.repositories.ban_repo import BanRepository
from app.services.ban_service import BanService
from app.schemas.ban_schemas import BanResponse,BanCreate
from app.services.notification_service import NotificationService
from app.repositories.notification_repo import NotificationRepository
from app.schemas.notification_schemas import NotificationResponse
from app.repositories.user_repo import UserRepository
from app.logger.log_config import logger
from app.schemas.spotify_schemas import SpotifyTrackDetails







class RoomService:

    @staticmethod
    def _map_room_to_response(room: Room) -> RoomResponse:
        """
        Преобразует объект модели Room в Pydantic-схему RoomResponse,
        включая информацию об участниках и очереди треков.
        """
        owner_response = UserService._map_user_to_response(room.user) if room.owner_id else None
        
        members_response = []
        if room.member_room:
            for member_association in room.member_room:
                if member_association.user:
                    members_response.append(UserService._map_user_to_response(member_association.user))

        queue_response = []
        if room.room_track:
            sorted_associations = sorted(room.room_track, key=lambda x: x.order_in_queue)
            for assoc in sorted_associations:
                if assoc.track:
                    queue_response.append(
                        TrackInQueueResponse(
                            track=TrackService._map_track_to_response(assoc.track),
                            order_in_queue=assoc.order_in_queue,
                            id=assoc.id,
                            added_at=assoc.added_at,
                        )
                    )

        room_data = RoomResponse(
            id=room.id,
            name=room.name,
            owner_id=room.owner_id,
            max_members=room.max_members,
            current_members_count=room.max_members, 
            is_private=room.is_private,
            created_at=room.created_at.isoformat() if room.created_at else None,
            current_track_id=room.current_track_id,
            current_track_position_ms=room.current_track_position_ms,
            is_playing=room.is_playing,
            owner=owner_response,
            members=members_response,
            queue=queue_response
        )
        return room_data
    
    
    @staticmethod
    def _map_member_to_response(member: Member_room_association) -> RoomMemberResponse:
        """
        Вспомогательный метод для маппинга Member_room_association (включая загруженный User)
        в Pydantic RoomMemberResponse.
        """
        return RoomMemberResponse.model_validate(member)
    
    

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
    async def create_room(db: Session,room_data: RoomCreate,owner: User) -> RoomResponse:
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
        try:
            new_room = RoomRepository.create_room(db,room_data_dict)
            db.flush()
            MemberRoomAssociationRepository.add_member(
                db,
                owner.id,
                new_room.id,
                role=Role.OWNER.value
            )
            db.commit()
            db.refresh(new_room)

            room_response = RoomService._map_room_to_response(new_room)
            websocket_message = {
            "action": "room_created",
            "room_data": room_response.model_dump_json()
            }
            await manager.broadcast(GLOBAL_ROOM_ID,websocket_message)

            return RoomService._map_room_to_response(new_room)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании комнаты: {e}"
            )
    

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
        
        try:
            updated_room_db = RoomRepository.update_room(db, room, data_to_update)
            
            db.commit()
            db.refresh(updated_room_db)

            return RoomService._map_room_to_response(updated_room_db)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при обновлении комнаты: {e}"
            )
    

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
        try:
            deleted_successfully = RoomRepository.delete_room(db,room_id)

            db.commit()

            if deleted_successfully:
                return {
                    'status': 'success',
                    'detail': 'Комната успешно удалена.',
                    'id': str(room_id),
                }
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось удалить комнату. {e}"
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
    async def join_room(db: Session,user: User,room_id: uuid.UUID,password: str | None = None) -> RoomResponse:
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
        global_ban = BanRepository.is_user_banned_global(db, user.id)
        if global_ban:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Вы забанены на платформе."
            )

        local_ban = BanRepository.is_user_banned_local(db, user.id, room_id)
        if local_ban:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Вы забанены в этой комнате."
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
        try:
            new_association = MemberRoomAssociationRepository.add_member(db,user.id,room_id,role=Role.MEMBER.value)

            db.commit()
            db.refresh(new_association)

            websocket_message_for_room = {
            "action": "join_room",
            "room_id": room.id,
            'user_id': user.id,
            'username': user.username,
            'detail': f'{user.username} присоелинился к комнате'
            }
            websocket_message_for_user = {
            "action": "join_room",
            "room_id": room.id,
            'user_id': user.id,
            'username': user.username,
            'detail': f'Вы присоединились к комнате {room.name}'
            }
            await manager.send_personal_message(json.dumps(websocket_message_for_user),user.id)
            await manager.broadcast(room_id,json.dumps(websocket_message_for_room))

            return RoomService._map_room_to_response(room)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось присоединиться к комнате. {e}"
            )

    @staticmethod
    async def leave_room(db: Session, room_id: uuid.UUID, user: User) -> dict[str, Any]:
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
                status_code=status.HTTP_409_CONFLICT,
                detail="Вы не являетесь участником этой комнаты."
            )
        try:
            deleted_successfully = MemberRoomAssociationRepository.remove_member(db,user.id,room_id)

            db.commit()

            websocket_message_for_room = {
            "action": "join_room",
            "room_id": room_id,
            'user_id': user.id,
            'username': user.username,
            'detail': f'{user.username} вышел из комнате'
            }
            websocket_message_for_user = {
            "action": "join_room",
            "room_id": room_id,
            'user_id': user.id,
            'username': user.username,
            'detail': f'Вы вышли из комнате{existing_association.room.name}'
            }
            await manager.send_personal_message(json.dumps(websocket_message_for_user),user.id)
            await manager.broadcast(room_id,json.dumps(websocket_message_for_room))

            if deleted_successfully:
                return {
                    'status': 'success',
                    'detail': f"Вы успешно покинули комнату с ID: {room_id}.",
                    'user_id': str(user.id),
                    'room_id': str(room_id)
                }
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось покинуть комнату.{e}"
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
        if not members:
            return []
        
        return [UserService._map_user_to_response(member) for member in members]
    

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
    

    @staticmethod
    async def add_track_to_queue(
        db: Session, 
        room_id: uuid.UUID,
        track_spotify_id: str, 
        current_user: User,
) -> RoomTrackAssociationModel:
        """
        Добавляет трек в очередь конкретной комнаты.
        """
        room = RoomRepository.get_room_by_id(db,room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail='Комната не найдена'
            )
        
        user_assoc = MemberRoomAssociationRepository.get_association_by_ids(db,current_user.id,room_id)

        if not user_assoc:
            raise HTTPException(
                status_code=404,
                detail=''
            )

        is_owner = (room.owner_id == current_user.id)
        is_moderator = (user_assoc and user_assoc.role == Role.MODERATOR.value)

        if not is_owner and not is_moderator:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас недостаточно прав.")
        
        track = TrackService.get_track_by_Spotify_id(db,track_spotify_id)
        if not track:
            raise TrackNotFoundException()
        
        dublicate_in_queue = RoomTrackAssociationRepository.get_association_by_room_and_track(db,room_id,track.id)
        if dublicate_in_queue:
            raise TrackAlreadyInQueueException()
        
        order_in_queue = RoomTrackAssociationRepository.get_last_order_in_queue(db,room_id)

        try:
            add_track = RoomTrackAssociationRepository.add_track_to_queue(db,room_id,track.id,order_in_queue,current_user.id)

            db.commit()
            db.refresh(add_track)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось добавить трек в очередь{e}."
            )
        try:
            updated_queue = RoomTrackAssociationRepository.get_queue_for_room(db, room_id)
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
    

    @staticmethod
    def get_room_queue(db: Session,room_id: uuid.UUID) -> list[TrackInQueueResponse]:
        """
        Получает текущую очередь треков для комнаты.
        """
        room = RoomRepository.get_room_by_id(db,room_id)
        if not room:
            raise RoomNotFoundException()
        
        queue_response = []
        if not room.room_track:
            return queue_response

        for assoc in room.room_track:
            if assoc.track:
                res = TrackInQueueResponse(
                    track=TrackService._map_track_to_response(assoc.track),
                    order_in_queue=assoc.order_in_queue,
                    id=assoc.id,
                    added_at=assoc.added_at
                )
                queue_response.append(res)
        

        return queue_response
    

    @staticmethod
    async def remove_track_from_queue(
        db: Session,
        room_id: uuid.UUID,
        association_id: uuid.UUID,
        current_user_id: uuid.UUID,
) -> dict[str,Any]:
        """
        Удаляет конкретный трек из очереди комнаты по ID ассоциации.
        """
        room = RoomRepository.get_room_by_id(db,room_id)
        if not room:
            raise RoomNotFoundException()
        
        user_assoc = MemberRoomAssociationRepository.get_association_by_ids(db,current_user_id,room_id)

        if not user_assoc:
            raise HTTPException(
                status_code=404,
                detail=''
            )

        is_owner = (room.owner_id == current_user_id)
        is_moderator = (user_assoc and user_assoc.role == Role.MODERATOR.value)

        if not is_owner and not is_moderator:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас недостаточно прав.")

        
        db_association = RoomTrackAssociationRepository.get_association_by_id(db,association_id)
        if not db_association or str(db_association.room_id) != str(room_id):
            raise ValueError("Ассоциация не найдена или не принадлежит этой комнате.")
        
        try:
            deleted_successfully = RoomTrackAssociationRepository.remove_track_from_queue_by_association_id(
                db,
                association_id
            )
            if deleted_successfully:
                RoomService._reorder_queue(db, room_id)
                db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось удалить трек из очередь{e}."
            )
        try:
            updated_queue = RoomTrackAssociationRepository.get_queue_for_room(db, room_id)
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
        

        
    @staticmethod
    def _reorder_queue(db: Session,room_id: uuid.UUID):
        """
        Переупорядочивает order_in_queue для всех оставшихся треков в очереди.
        """
        queue_association = db.query(RoomTrackAssociationModel).where(
            RoomTrackAssociationModel.room_id == room_id,
        ).order_by(RoomTrackAssociationModel.order_in_queue).all()

        try:
            for index,assoc in enumerate(queue_association):
                assoc.order_in_queue = index
                db.add(assoc)

            db.flush()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f'Не удалось перепорядочить очередь.{e}'
            )


    @staticmethod
    async def move_track_in_queue(db: Session,room_id: uuid.UUID,association_id: uuid.UUID,current_user: User,new_position: int,) -> RoomTrackAssociationModel:
        """Перемещает трек в очереди."""
        room = RoomRepository.get_room_by_id(db,room_id)
        if not room:
            raise RoomNotFoundException()
        
        if room.owner_id != current_user.id:
            raise  UnauthorizedRoomActionException()
        
        queue = RoomTrackAssociationRepository.get_queue_for_room(db,room_id)
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
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f'Не удалось перепорядочить очередь.{e}'
            )

        try:
            updated_queue = RoomTrackAssociationRepository.get_queue_for_room(db, room_id)
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
    

    @staticmethod
    async def set_playback_host(db: Session, room_id: uuid.UUID, user_id: uuid.UUID) -> RoomResponse:
        """
        Назначает пользователя хостом воспроизведения для комнаты.
        Пользователь должен быть членом комнаты и иметь авторизацию Spotify с активным устройством.
        """
        pass

    @staticmethod
    async def clear_playback_host(db: Session, room_id: uuid.UUID) -> RoomResponse:
        """
        Очищает хоста воспроизведения для комнаты и сбрасывает состояние плеера.
        """
        pass

    @staticmethod
    async def update_room_playback_state(
        db: Session, 
        room_id: uuid.UUID, 
        current_playing_track_assoc_id: uuid.UUID | None, 
        progress_ms: int, 
        is_playing: bool
    ) -> RoomResponse:
        """
        Обновляет состояние воспроизведения в полях комнаты. 
        Используется, например, планировщиком или при получении состояния плеера от хоста.
        """
        pass

    @staticmethod
    async def player_command_play(
        db: Session,
        room_id: uuid.UUID,
        current_user: User,
        track_uri: str| None = None,
        position_ms: int = 0
    ) -> dict[str, Any]:
        """
        Отправляет команду "PLAY" на Spotify плеер комнаты через хоста воспроизведения.
        """
        pass

    @staticmethod
    async def player_command_pause(
        db: Session,
        room_id: uuid.UUID,
        current_user: User
    ) -> dict[str, Any]:
        """
        Отправляет команду "PAUSE" на Spotify плеер комнаты через хоста воспроизведения.
        """
        pass

    @staticmethod
    async def player_command_skip_next(
        db: Session,
        room_id: uuid.UUID,
        current_user: User
    ) -> dict[str, Any]:
        """
        Отправляет команду "SKIP NEXT" на Spotify плеер комнаты через хоста воспроизведения.
        """
        pass

    @staticmethod
    async def player_command_skip_previous(
        db: Session,
        room_id: uuid.UUID,
        current_user: User
    ) -> dict[str, Any]:
        """
        Отправляет команду "SKIP PREVIOUS" на Spotify плеер комнаты через хоста воспроизведения.
        """
        pass

    @staticmethod
    async def get_room_player_state(
        db: Session, 
        room_id: uuid.UUID, 
        current_user: User
    ) -> dict[str, Any]:
        """
        Получает текущее состояние Spotify плеера для комнаты.
        """
        pass


    
    @staticmethod
    async def update_member_role(
        db: Session,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: Role,
        current_user: User,
    ) -> RoomMemberResponse:
        """
        Изменяет роль члена комнаты. Только владелец комнаты может это делать.

        Args:
            db (Session): Сессия базы данных.
            room_id (uuid.UUID): ID комнаты.
            target_user_id (uuid.UUID): ID пользователя, чью роль нужно изменить.
            new_role (str): Новая роль для пользователя.
            current_user_id (uuid.UUID): ID текущего аутентифицированного пользователя (владельца).

        Returns:
            RoomMemberResponse: Обновленная информация о члене комнаты.

        Raises:
            HTTPException: Если комната не найдена, пользователь не авторизован,
                           целевой пользователь не является членом комнаты,
                           или роль недействительна.
        """
        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена.")


        current_user_association = MemberRoomAssociationRepository.get_association_by_ids(
            db, current_user.id, room_id
        )
        if not current_user_association or current_user_association.role != Role.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для изменения ролей в этой комнате. Только владелец может это делать."
            )
        
            
        target_user_association = MemberRoomAssociationRepository.get_association_by_ids(
            db, target_user_id, room_id
        )
        if not target_user_association:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Целевой пользователь не является членом этой комнаты."
            )
        
        
        if target_user_id == current_user.id and new_role != Role.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Владелец не может изменить свою собственную роль на не-владельца напрямую через этот метод."
            )
            

        if target_user_id == room.owner_id and new_role != Role.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя разжаловать создателя комнаты."
            )
            

        if target_user_association.role == new_role.value: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Пользователь уже имеет такую роль.'
            )
        
        try:
            updated_association = MemberRoomAssociationRepository.update_role(
                db, target_user_id, room_id, new_role.value
            )
            
            if not updated_association:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Не удалось обновить роль члена комнаты."
                )

            db.commit() 
            
            final_association_for_response = MemberRoomAssociationRepository.get_association_by_ids(
                db, target_user_id, room_id
            )
            if not final_association_for_response:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при формировании ответа после обновления роли."
                )
            
            role_message_for_room = {
                'room_id': room_id,
                'username': target_user_association.user.username,
                'new_role': target_user_association.role,
                'moderator_id': current_user.id,
                'moderator_username': current_user.username,
                'detail': f'У пользователя {target_user_association.user.username} была обновлена роль до {target_user_association.role}'
            }
            role_message_for_user = {
                'room_id': room_id,
                'username': target_user_association.user.username,
                'new_role': target_user_association.role,
                'moderator_id': current_user.id,
                'moderator_username': current_user.username,
                'detail': f'У вас была обновлена роль до {new_role.value}'
            }
            await manager.send_personal_message(json.dumps(role_message_for_user))
            await manager.broadcast(room_id,json.dumps(role_message_for_room))

            return RoomService._map_member_to_response(final_association_for_response)

        except HTTPException as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка сервера при изменении роли: {e}"
            )
        

    @staticmethod
    async def kick_member_from_room(db: Session,room_id: uuid.UUID,user_id: uuid.UUID,current_user: User) -> dict[str,Any]:
        """
        Удаляет указанного пользователя из комнаты. 🚪

        Эту операцию могут выполнять только владелец или модератор комнаты.
        Модераторы не могут кикать владельцев или других модераторов.
        Пользователь не может кикнуть самого себя.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): Уникальный ID комнаты, из которой нужно удалить пользователя.
            user_id (uuid.UUID): Уникальный ID пользователя, которого нужно кикнуть.
            current_user (User): Объект текущего аутентифицированного пользователя,
                                который пытается выполнить действие (должен быть владельцем или модератором).

        Returns:
            dict[str, Any]: Словарь с подтверждением успешного удаления пользователя.

        Raises:
            HTTPException (404 NOT FOUND): Если комната не найдена, или целевой пользователь не является членом комнаты.
            HTTPException (403 FORBIDDEN): Если у текущего пользователя недостаточно прав (он не владелец/модератор),
                                        или модератор пытается кикнуть владельца/другого модератора,
                                        или пытаются кикнуть владельца комнаты.
            HTTPException (400 BAD REQUEST): Если пользователь пытается кикнуть самого себя.
            HTTPException (500 INTERNAL SERVER ERROR): При внутренних ошибках сервера во время операции.
        """
        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена.")


        current_user_association = MemberRoomAssociationRepository.get_association_by_ids(
            db, current_user.id, room_id
        )
        if not current_user_association or current_user_association.role not in [Role.OWNER.value, Role.MODERATOR.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для изменения ролей в этой комнате. Только владелец и модератор может это делать."
            )
        
        
        target_user_association = MemberRoomAssociationRepository.get_association_by_ids(
            db, user_id, room_id
        )
        if not target_user_association: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Пользователь, которого вы пытаетесь кикнуть, не найден в этой комнате."
        )
        if current_user.id == user_id:
                raise HTTPException(
                    status_code=400,
                    detail='Нельзя кикнуть себя'
        )
        if user_id == room.owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Владельца нельяза кикнуть из комнаты."
        )
        
        
        if current_user_association.role == Role.MODERATOR.value:
            if target_user_association.role == Role.MODERATOR.value:
                raise HTTPException(
                    status_code=403,
                    detail='Нельзя кикнуть модератора'
                )
            elif target_user_association.role == Role.OWNER.value:
                raise HTTPException(
                    status_code=403,
                    detail='Нельзя кикнуть Владельца'
                )
            
        
        try:
            kick_message_for_room = {
                'action': 'you_weke_kicked',
                'kicked_user_id': user_id,
                'kicked_username': target_user_association.user.username,
                'room_id': room_id,
                'moderator_id': current_user.id,
                'detail': f'Пользователь {target_user_association.user.username} был кикнут из комнаты.'
            }
            kick_message_for_user = {
                'action': 'user_kicked_from_room',
                'kicked_user_id': user_id,
                'kicked_username': target_user_association.user.username,
                'room_id': room_id,
                'moderator_id': current_user.id,
                'detail': f'Вы были кикнуты из комнаты {room.name}'
            }
            MemberRoomAssociationRepository.remove_member(db,user_id,room_id)
            db.commit()
            
            await manager.send_personal_message(json.dumps(kick_message_for_user),user_id)
            await manager.broadcast(room_id,json.dumps(kick_message_for_room))
            return {
                'action': 'kick member',
                'status': 'success',
                'user_id': user_id,
                'room_id': room_id,
            }
            
        except HTTPException as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка сервера при кике пользователя: {e}"
            )


    @staticmethod
    async def ban_user_from_room(
        db: Session,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        ban_data: BanCreate,
        current_user: User, 
    ) -> BanResponse:
        """
        Банит пользователя в конкретной комнате или глобально.
        Только владелец комнаты может банить других пользователей.
        Модераторы НЕ могут банить.

        Args:
            db (Session): Сессия базы данных.
            room_id (uuid.UUID): ID комнаты.
            target_user_id (uuid.UUID): ID пользователя, которого нужно забанить.
            ban_data (BanCreate): Данные для бана (причина, room_id).
            current_user (User): Текущий аутентифицированный пользователь, выполняющий действие.
            manager (Any): Экземпляр ConnectionManager для WebSocket-уведомлений.

        Returns:
            BanResponse: Объект BanResponse, представляющий созданный бан.

        Raises:
            HTTPException: Если комната не найдена, недостаточно прав,
                           целевой пользователь не найден, пользователь уже забанен,
                           или произошла внутренняя ошибка.
        """
        try:
            room = RoomRepository.get_room_by_id(db, room_id)
            if not room:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена.")

            current_user_assoc = MemberRoomAssociationRepository.get_association_by_ids(
                db, current_user.id, room_id
            )
            if not current_user_assoc or current_user_assoc.role != Role.OWNER.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав для бана пользователей в этой комнате. Только владелец может банить."
                )
            
            
            if current_user.id == target_user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы не можете забанить самого себя.")


            existing_global_ban = BanRepository.is_user_banned_global(db, target_user_id)
            if existing_global_ban:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь уже забанен глобально.")
            
            existing_local_ban = BanRepository.is_user_banned_local(db, target_user_id, room_id)
            if existing_local_ban:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь уже забанен в этой комнате.")

            existing_member_association = MemberRoomAssociationRepository.get_association_by_ids(db, target_user_id, room_id)
            if existing_member_association:
                removed_from_room = MemberRoomAssociationRepository.remove_member(db, target_user_id, room_id)
                if not removed_from_room:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось подготовить пользователя к бану.")
                db.flush()

            new_ban_entry = BanRepository.add_ban(
                db=db,
                ban_user_id=target_user_id,
                room_id=room_id,
                reason=ban_data.reason,
                by_ban_user_id=current_user.id
            )

            db.commit()
            db.refresh(new_ban_entry)


            ban_notification_for_room = {
                "action": "ban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "banned_by": str(current_user.id),
                "reason": ban_data.reason if ban_data.reason else "не указана",
                "detail": f"Пользователь {target_user_id} был забанен в комнате."
            }
            ban_notification_for_user = {
                "action": "ban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "banned_by": str(current_user.id),
                "reason": ban_data.reason if ban_data.reason else "не указана",
                "detail": f"Вы были забанены в комнате {room.name}."
            }
            await manager.send_personal_message(json.dumps(ban_notification_for_user),target_user_id)
            await manager.broadcast(room_id, json.dumps(ban_notification_for_room))
            
            
            return BanService._map_ban_to_response(new_ban_entry)

        except HTTPException as e:
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось забанить пользователя из-за внутренней ошибки сервера."
            )

    @staticmethod
    async def unban_user_from_room(
        db: Session,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        current_user: User,
    ) -> dict[str, Any]:
        """
        Снимает бан с пользователя в конкретной комнате.
        Только владелец комнаты может снимать баны.

        Args:
            db (Session): Сессия базы данных.
            room_id (uuid.UUID): ID комнаты.
            target_user_id (uuid.UUID): ID пользователя, с которого нужно снять бан.
            current_user (User): Текущий аутентифицированный пользователь, выполняющий действие.
            manager (Any): Экземпляр ConnectionManager для WebSocket-уведомлений.

        Returns:
            dict[str, Any]: Сообщение об успешном снятии бана.

        Raises:
            HTTPException: Если комната не найдена, недостаточно прав,
                           пользователь не забанен, или произошла внутренняя ошибка.
        """
        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена.")

        current_user_assoc = MemberRoomAssociationRepository.get_association_by_ids(
            db, current_user.id, room_id
        )
        if not current_user_assoc or current_user_assoc.role != Role.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для снятия банов в этой комнате. Только владелец может снимать баны."
            )
        
        if current_user.id == target_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы не можете снять бан с самого себя.")


        existing_ban_to_unban = BanRepository.is_user_banned_local(db, target_user_id, room_id)
        if not existing_ban_to_unban:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не забанен в этой комнате."
            )
        try:
            unbanned_successfully = BanRepository.remove_ban_local(db, target_user_id, room_id)
            
            if not unbanned_successfully:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось снять бан из-за внутренней ошибки сервера.")
            
            db.commit()

            unban_notification_for_room = {
                "action": "unban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "unbanned_by": str(current_user.id),
                "detail": f"Бан пользователя {target_user_id} в комнате снят."
            }
            unban_notification_for_user = {
                "action": "unban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "unbanned_by": str(current_user.id),
                "detail": f"Ваш бан в комнате{room.name} снят."
            }
            await manager.send_personal_message(json.dumps(unban_notification_for_user),target_user_id)
            await manager.broadcast(room_id, json.dumps(unban_notification_for_room))

            return {
                "status": "success",
                "detail": f"Бан с пользователя {target_user_id} в комнате {room_id} успешно снят."
            }

        except HTTPException as e:
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось снять бан из-за внутренней ошибки сервера."
            )
        
    
    @staticmethod
    async def send_room_invite(
        db: Session,
        room_id: uuid.UUID,
        inviter_id: uuid.UUID,
        invited_user_id: uuid.UUID,
    ) -> dict[str,str]:
        """
        Отправляет приглашение в комнату указанному пользователю.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты, куда приглашают.
            inviter_id (uuid.UUID): ID пользователя, который отправляет приглашение.
            invited_user_id (uuid.UUID): ID пользователя, которого приглашают.

        Returns:
            dict[str, str]: Сообщение об успешной отправке приглашения.

        Raises:
            HTTPException: Если комната/пользователи не найдены, права недостаточны,
                           или приглашение невозможно отправить по другим причинам.
        """
        room = RoomRepository.get_room_by_id(db,room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail='Комната не найдена'
            )
        inviter = UserRepository.get_user_by_id(db,inviter_id)
        if not inviter:
            raise HTTPException(
                status_code=404,
                detail='Приглашающий пользователь не найден'
            )
        
        invited = UserRepository.get_user_by_id(db,invited_user_id)
        if not invited:
            raise HTTPException(
                status_code=404,
                detail='Приглашаемый пользователь не найден'
            )
        
        if inviter_id == invited_user_id:
            raise HTTPException(
                status_code=400,
                detail='Вы не можете пригласить самого себя в комнату.'
            )
        
        inviter_membership = MemberRoomAssociationRepository.get_member_room_association(db, room_id, inviter_id)
        if not inviter_membership or inviter_membership.role not in [Role.OWNER, Role.MODERATOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='У вас нет прав для приглашения пользователей в эту комнату. Только владельцы и модераторы могут это делать.'
            )

        invited_member_in_room = MemberRoomAssociationRepository.get_member_room_association(db, room_id, invited_user_id)
        if invited_member_in_room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Пользователь уже является участником этой комнаты.'
            )
            
        have_banned = BanRepository.is_user_banned_local(db,invited_user_id,room_id)
        if have_banned:
            raise HTTPException(
                status_code=403,
                detail='Пользователь забанен в этой комнате'
            )
        
        try:
            NotificationService.add_notification(
                db,
                invited_user_id,
                NotificationType.ROOM_INVITE,
                message=f"{inviter.username} приглашает вас в комнату {room.name}.",
                inviter_id=inviter_id,
                room_id=room_id,
                related_object_id=room_id
            )
            ws_message = {
                'action': 'room_invite_received',
                'room_id': str(room_id),
                'room_name': room.name,
                'inviter_id': str(inviter_id),
                'inviter_username': inviter.username,
                'detail': f"Вы получили приглашение в комнату {room.name} от {inviter.username}."
            }
            await manager.send_personal_message(json.dumps(ws_message),invited_user_id)
            return {"status": "success", "detail": "Приглашение отправлено."}
        except HTTPException as e:
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось создать уведомление из-за внутренней ошибки сервера."
            )


    @staticmethod
    async def handle_room_invite_response(
        db: Session,
        notification_id: uuid.UUID,
        current_user_id: uuid.UUID,
        action: NotificationType,
    ) -> NotificationResponse:
        """
        Обрабатывает ответ пользователя на приглашение в комнату (принять или отклонить).

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            notification_id (uuid.UUID): ID уведомления о приглашении.
            current_user_id (uuid.UUID): ID текущего пользователя, который отвечает на приглашение.
            action (str): Действие пользователя ("accept" для принятия, "decline" для отклонения).

        Returns:
            dict[str, str]: Сообщение о результате операции.

        Raises:
            HTTPException: Если уведомление не найдено, у пользователя нет прав,
                           уведомление не является приглашением, или возникла другая ошибка.
        """
        notification = NotificationRepository.get_notification_by_id(db,notification_id)
        if not notification:
            raise HTTPException(
                status_code=404,
                detail='Уведомление не найдено'
            )
        
        if not notification.user_id == current_user_id:
            raise HTTPException(
                status_code=403,
                detail='Это уведомление принадлежит не вам'
            )
        
        if not notification.notification_type != NotificationType.ROOM_INVITE:
            raise HTTPException(
                status_code=400,
                detail='Это уведомление не является приглашением в комнату.'
            )
        
        if not notification.is_read:
            raise HTTPException(
                status_code=400,
                detail='Это приглашение уже было обработано.'
            )
        
        room_id = notification.room_id
        inviter_id = notification.sender_id
        invited_user_id = notification.user_id 

        try:
            room = RoomRepository.get_room_by_id(db, room_id)
            if not room:
                NotificationService.mark_notification_as_read(db, notification_id, current_user_id)
                db.commit() 
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Комната, в которую вас пригласили, не найдена или удалена.'
                )
            
            inviter = UserRepository.get_user_by_id(db, inviter_id) if inviter_id else None
            invited_user = UserRepository.get_user_by_id(db, invited_user_id)


            if action == "accept":
                invited_member_in_room = MemberRoomAssociationRepository.get_member_room_association(db, room_id, invited_user_id)
                if invited_member_in_room:
                    NotificationService.mark_notification_as_read(db, notification_id, current_user_id) # Помечаем как прочитанное
                    db.commit() 
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='Вы уже являетесь участником этой комнаты.'
                    )
                
                is_banned_local = BanRepository.is_user_banned_local(db, invited_user_id, room_id)
                if is_banned_local:
                    NotificationService.mark_notification_as_read(db, notification_id, current_user_id) # Помечаем как прочитанное
                    db.commit() 
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail='Вы забанены в этой комнате и не можете присоединиться.'
                    )
                
                new_member_association = MemberRoomAssociationRepository.add_member(
                    db, invited_user_id,room_id,Role.MEMBER 
                )
                
                NotificationService.mark_notification_as_read(db, notification_id, current_user_id)

                db.commit()
                db.refresh(new_member_association)

                websocket_message = {
                    "action": "user_joined_room",
                    "room_id": str(room_id),
                    "user_id": str(invited_user_id),
                    "username": invited_user.username,
                    "detail": f"{invited_user.username} присоединился(ась) к комнате."
                }
                await manager.broadcast(room_id, json.dumps(websocket_message))

                if inviter:
                    NotificationService.add_notification(
                        db=db,
                        user_id=inviter_id,
                        notification_type=NotificationType.SYSTEM_MESSAGE, 
                        message=f"{invited_user.username} принял(а) ваше приглашение в комнату {room.name}.",
                        sender_id=invited_user_id, 
                        room_id=room_id,
                        related_object_id=room_id
                    )
                
                return {"status": "success", "detail": "Вы успешно присоединились к комнате."}

            elif action == "decline":
                NotificationService.mark_notification_as_read(db, notification_id, current_user_id)
                db.commit()

                if inviter:
                    await NotificationService.add_notification(
                        db=db,
                        user_id=inviter_id,
                        notification_type=NotificationType.SYSTEM_MESSAGE, 
                        message=f"{invited_user.username} отклонил(а) ваше приглашение в комнату {room.name}.",
                        sender_id=invited_user_id,
                        room_id=room_id,
                        related_object_id=room_id
                    )
                return {"status": "success", "detail": "Приглашение отклонено."}

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Недопустимое действие. Действие должно быть "accept" или "decline".'
                )

        except HTTPException as e:
            db.rollback()
            raise e
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось обработать приглашение из-за внутренней ошибки сервера."
            )
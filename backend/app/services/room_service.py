from fastapi import HTTPException,status
from app.repositories.room_repo import RoomRepository
from app.repositories.member_room_association_repo import MemberRoomAssociationRepository
from sqlalchemy.orm import Session
from app.schemas.room_schemas import RoomResponse, RoomCreate, RoomUpdate,TrackInQueueResponse
from app.schemas.user_schemas import UserResponse
from app.services.user_service import UserService
from app.models.room import Room
from app.models.track import Track
from app.services.track_service import TrackService
from app.services.spotify_sevice import SpotifyService
import uuid
from typing import Any
from app.utils.hash import make_hash_pass,verify_pass
from app.models.user import User
from app.models.room_track_association import RoomTrackAssociationModel
from app.models.room_track_association import RoomTrackAssociationModel
from app.repositories.room_track_association_repo import RoomTrackAssociationRepository
from app.exceptions.exception import (
    TrackNotFoundException, 
    TrackAlreadyInQueueException, 
    RoomNotFoundException,
    UnauthorizedRoomActionException
)
from enum import Enum
from app.ws.connection_manager import manager
import json
from app.services.google_service import GoogleService
from app.services.spotify_public_service import SpotifyPublicService


class ControlAction(Enum):
    PLAY = 'play'
    PAUSE = 'pause'
    SKIP = 'skip'



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
                status_code=status.HTTP_409_CONFLICT,
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
        
        if room.owner_id != current_user.id:
            raise UnauthorizedRoomActionException()
        
        track = TrackService.get_track_by_Spotify_id(db,track_spotify_id)
        if not track:
            raise TrackNotFoundException()
        
        dublicate_in_queue = RoomTrackAssociationRepository.get_association_by_room_and_track(db,room_id,track.id)
        if dublicate_in_queue:
            raise TrackAlreadyInQueueException()
        
        order_in_queue = RoomTrackAssociationRepository.get_last_order_in_queue(db,room_id)

        add_track = RoomTrackAssociationRepository.add_track_to_queue(db,room_id,track.id,order_in_queue,current_user.id)

        db.commit()
        db.refresh(add_track)
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
                        "artist": assoc.track.artist,
                        "album_art_url": assoc.track.album
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
) -> bool:
        """
        Удаляет конкретный трек из очереди комнаты по ID ассоциации.
        """
        room = RoomRepository.get_room_by_id(db,room_id)
        if not room:
            raise RoomNotFoundException()
        

        if room.owner_id != current_user_id:
            raise UnauthorizedRoomActionException()
        
        db_association = RoomTrackAssociationRepository.get_association_by_id(db,association_id)
        if not db_association or str(db_association.room_id) != str(room_id):
            raise ValueError("Ассоциация не найдена или не принадлежит этой комнате.")
        
        deleted_successfully = RoomTrackAssociationRepository.remove_track_from_queue_by_association_id(
            db,
            association_id
        )
        if deleted_successfully:
            RoomService._reorder_queue(db, room_id)
            db.commit()
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
                            "artist": assoc.track.artist,
                            "album_art_url": assoc.track.album
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
        else:
            return {
                'status': 'failed',
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


        for index,assoc in enumerate(queue_association):
            assoc.order_in_queue = index
            db.add(assoc)

        db.flush()


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
    
        queue.remove(track_to_move)

        queue.insert(new_position, track_to_move)

        for index, assoc in enumerate(queue):
            assoc.order_in_queue = index
        
        db.commit()

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
                        "artist": assoc.track.artist,
                        "album_art_url": assoc.track.album
                    } for assoc in updated_queue
                ]
            }
            await manager.broadcast(room_id, json.dumps(update_message))
        except Exception as e:
            print(f"Ошибка при отправке WebSocket-сообщения: {e}")

        return {"message": "Трек успешно перемещён."}
    

    @staticmethod
    async def control_player(db: Session, room_id: uuid.UUID, action: str, current_user: User):
        """
        Отправляет команды управления плеером Spotify и оповещает клиентов через WebSocket.
        """
        room = RoomRepository.get_room_by_id(db, room_id)
        if not room:
            raise RoomNotFoundException()
        
        if room.owner_id != current_user.id:
            raise UnauthorizedRoomActionException()
        
        if not current_user.spotify_access_token:
            raise HTTPException(
                status_code=401,
                detail='Пользователь не авторизован в Spotify.'
            )
        
        spotify = SpotifyService(db, current_user)
        
        device_id = await spotify._get_device_id(current_user.spotify_access_token)
        if not device_id:
            raise HTTPException(
                status_code=400,
                detail='Активное устройство Spotify не найдено.'
            )

        try:
            if action == ControlAction.PLAY.value:
                if not room.current_track_id:
                    first_track_in_queue = RoomTrackAssociationRepository.get_first_track_in_queue(db, room_id)
                    if first_track_in_queue:
                        room.current_track_id = first_track_in_queue.track_id
                        room.is_playing = True
                    else:
                        raise ValueError("В очереди нет треков для воспроизведения.")
                
                if room.current_track_id:
                    track = room.current_track
                    if track:
                        await spotify.play(
                            track_uri=track.spotify_uri,
                            device_id=device_id
                        )
                    else:
                        raise ValueError("Трек не найден в базе данных.")
                
                db.commit()

            elif action == ControlAction.PAUSE.value:
                await spotify.pause(current_user.spotify_access_token,device_id=device_id)
                room.is_playing = False
                
                db.commit()

            elif action == ControlAction.SKIP.value:
                await spotify.skip(current_user.spotify_access_token,device_id=device_id)
                
                if room.current_track_id:
                    current_association_to_remove = RoomTrackAssociationRepository.get_association_by_room_and_track(
                        db, 
                        room_id=room_id,
                        track_id=room.current_track_id
                    )
                    if current_association_to_remove:
                        RoomTrackAssociationRepository.remove_track_from_queue_by_association_id(
                            db, 
                            association_id=current_association_to_remove.id
                        )
                        RoomService._reorder_queue(db, room_id)
                
                room.current_track_id = None
                room.is_playing = False
                
                db.commit()

            else:
                raise ValueError(f"Неизвестное действие: {action}")

            update_message = {
                "action": action,
                "is_playing": room.is_playing,
                "current_track_id": str(room.current_track_id) if room.current_track_id else None
            }
            await manager.broadcast(room_id, json.dumps(update_message))

        except HTTPException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=f"Ошибка Spotify: {e.detail}"
            )
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Внутренняя ошибка сервера: {e}"
            )
        
        return {"detail": f"Команда '{action}' успешно выполнена."}


    

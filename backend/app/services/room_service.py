import uuid

from app.logger.log_config import logger
from app.schemas.entity import UserEntity
from app.repositories.abc.member_room_association import ABCMemberRoomAssociationRepository
from app.repositories.abc.room_repo import ABCRoomRepository

from app.schemas.enum import Role
from app.schemas.room_schemas import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)

from app.auth.hash import make_hash_pass
from app.ws.connection_manager import manager
from app.services.mappers.room_mapper import RoomMapper

from app.exceptions.exception import ServerError
from app.exceptions.room_exception import (
    RoomAlreadyExistsError,
    RoomNotFoundError,
    RoomPermissionDeniedError,
    PublicRoomCannotHavePasswordError,
    PrivateRoomRequiresPasswordError,
)


class RoomService:
    """
    Реализует бизнес логику для работы с комнатами
    """

    def __init__(
        self,
        room_repo: ABCRoomRepository,
        member_room_repo: ABCMemberRoomAssociationRepository,
        room_mapper: RoomMapper,
    ):
        self.room_repo = room_repo
        self.member_room_repo = member_room_repo
        self.room_mapper = room_mapper

    async def get_room_by_id(self, room_id: uuid.UUID) -> RoomResponse:
        """
        Получает комнату по ее уникальному ID.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        return self.room_mapper.to_response(room)

    async def get_room_by_name(self, name: str) -> RoomResponse:
        """
        Получает комнату по ее названию.
        """
        room = self.room_repo.get_room_by_name(name)
        if not room:
            raise RoomNotFoundError()

        return self.room_mapper.to_response(room)

    async def get_all_rooms(self) -> list[RoomResponse]:
        """
        Получает список всех комнат из базы данных.
        """
        rooms_list = self.room_repo.get_all_rooms()

        return [self.room_mapper.to_response(room) for room in rooms_list]

    async def create_room(self, room_data: RoomCreate, owner: UserEntity) -> RoomResponse:
        """
        Создает новую комнату.
        Включает проверку уникальности имени и хэширование пароля.
        """

        room = self.room_repo.get_room_by_name(room_data.name)
        if room:
            raise RoomAlreadyExistsError(
                detail=f"Комната с названием '{room_data.name}' уже существует."
            )

        room_data_dict = room_data.model_dump()
        room_data_dict["owner_id"] = owner.id

        if room_data.is_private:
            if not room_data.password:
                raise PrivateRoomRequiresPasswordError()
            room_data_dict["password"] = make_hash_pass(room_data.password)
        room_data_dict["password_hash"] = None
        if room_data.password:
            raise PublicRoomCannotHavePasswordError()

        room_data_dict.pop("password", None)
        try:
            new_room = self.room_repo.create_room(room_data_dict)

            self.member_room_repo.add_member(
                owner.id, new_room.id, role=Role.OWNER.value
            )

            room_response = self.room_mapper.to_response(new_room)
            websocket_message = {
                "action": "room_created",
                "room_data": room_response.model_dump_json(),
            }
            await manager.broadcast(manager.GLOBAL_ROOM_ID, websocket_message)

            return self.room_mapper.to_response(new_room)
        except Exception as e:
            raise ServerError(
                detail=f"Ошибка при создании комнаты: {e}",
            )

    def update_room(
        self, room_id: uuid.UUID, update_data: RoomUpdate, current_user: UserEntity
    ) -> RoomResponse:
        """
        Обновляет существующую комнату.
        Только владелец комнаты может ее обновить.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        if room.owner_id != current_user.id:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для обновления этой комнаты.",
            )

        data_to_update = update_data.model_dump(exclude_unset=True)

        if "is_private" in data_to_update:
            if data_to_update["is_private"] and "password" not in data_to_update:
                raise PrivateRoomRequiresPasswordError(
                    detail="Для установки приватности комнаты требуется новый пароль.",
                )
            elif (
                not data_to_update["is_private"]
                and "password" in data_to_update
                and data_to_update["password"] is not None
            ):
                raise PublicRoomCannotHavePasswordError(
                    detail="Пароль не может быть установлен для не приватной комнаты.",
                )

        if "password" in data_to_update and data_to_update["password"] is not None:
            data_to_update["password_hash"] = make_hash_pass(
                data_to_update.pop("password")
            )
        elif "password" in data_to_update and data_to_update["password"] is None:
            data_to_update["password_hash"] = None

        try:
            updated_room_db = self.room_repo.update_room(room, data_to_update)

            return self.room_mapper.to_response(updated_room_db)
        except Exception as e:

            raise ServerError(
                detail=f"Ошибка при обновлении комнаты: {e}",
            )

    def delete_room(self, room_id: uuid.UUID, owner: UserEntity) -> dict[str, str]:
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
            raise RoomNotFoundError()

        if room.owner_id != owner.id:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для обновления этой комнаты.",
            )
        try:
            deleted_successfully = self.room_repo.delete_room(room_id)

            if deleted_successfully:
                return {
                    "status": "success",
                    "detail": "Комната успешно удалена.",
                    "id": str(room_id),
                }
        except Exception as e:

            raise ServerError(
                detail=f"Не удалось удалить комнату. {e}",
            )

    async def get_user_rooms(self, user: UserEntity) -> list[RoomResponse]:
        """
        Получает список всех комнат, в которых состоит данный пользователь.

        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
            user (User): Объект текущего пользователя.

        Returns:
            List[RoomResponse]: Список объектов RoomResponse, в которых состоит пользователь.
        """
        rooms = self.member_room_repo.get_rooms_by_user_id(user.id)
        return [self.room_mapper.to_response(room) for room in rooms]

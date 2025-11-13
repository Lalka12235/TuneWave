import json
import uuid

from app.config.log_config import logger
from app.domain.entity.user import UserEntity
from app.domain.interfaces.ban_repo import BanRepository
from app.domain.interfaces.member_room_association import MemberRoomAssociationRepository
from app.domain.interfaces.room_repo import RoomRepository
from app.domain.interfaces.user_repo import UserRepository

from app.presentation.schemas.ban_schemas import BanCreate, BanResponse
from app.domain.enum import NotificationType, Role
from app.presentation.schemas.notification_schemas import NotificationResponse
from app.presentation.schemas.room_member_schemas import RoomMemberResponse
from app.presentation.schemas.room_schemas import RoomResponse


from app.application.mappers.mappers import (
    RoomMapper,
    UserMapper,
    BanMapper,
    RoomMemberMapper,
)
from app.domain.interfaces.notification_repo import NotificationRepository

from app.presentation.auth.hash import verify_pass
from app.infrastructure.ws.connection_manager import manager
from app.presentation.schemas.user_schemas import UserResponse

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    UserInRoomError,
    UserNotInRoomError,
    InvalidRoomPasswordError,
    RoomPermissionDeniedError,
    SelfInteractionError,
    RoleConflictError,
    OwnerRoleChangeError,
    InvalidActionError,
)
from app.domain.exceptions.ban_exception import UserBannedGlobal, UserBannedInRoom,UserNotExistingBan
from app.domain.exceptions.user_exception import UserNotFound
from app.domain.exceptions.notification_exception import NotificationNotPermission,NotificationTypeError,NotificationStateError

class RoomMemberService:
    """
    Реализует бизнес логику для работы с участниками комнаты
    """

    def __init__(
        self,
        room_repo: RoomRepository,
        user_repo: UserRepository,
        member_room_repo: MemberRoomAssociationRepository,
        ban_repo: BanRepository,
        notify_repo: NotificationRepository,
        room_mapper: RoomMapper,
        user_mapper: UserMapper,
        ban_mapper: BanMapper,
        room_member_mapper: RoomMemberMapper,
    ):
        self.room_repo = room_repo
        self.user_repo = user_repo
        self.member_room_repo = member_room_repo
        self.ban_repo = ban_repo
        self.notify_repo = notify_repo
        self.room_mapper = room_mapper
        self.user_mapper = user_mapper
        self.ban_mapper = ban_mapper
        self.room_member_mapper = room_member_mapper

    def verify_room_password(room: RoomEntity, password: str) -> bool:
        """
        Проверяет предоставленный пароль для приватной комнаты.
        """
        if not room.is_private or not room.password_hash:
            return False

        return verify_pass(password, room.password_hash)

    async def join_room(
        self, user: UserEntity, room_id: uuid.UUID, password: str | None = None
    ) -> RoomResponse:
        """
        Пользователь присоединяется к комнате.

        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты, к которой присоединяется пользователь.
            user (User): Объект текущего пользователя.
            password (Optional[str]): Пароль для приватной комнаты.

        Returns:
            RoomResponse: Объект комнаты, к которой присоединился пользователь.

        Raises:
            HTTPException: Если комната не найдена, пользователь уже является участником,
                           неверный пароль, или комната переполнена.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        global_ban = self.ban_repo.is_user_banned_global(user.id)
        if global_ban:
            raise UserBannedGlobal()

        local_ban = self.ban_repo.is_user_banned_local(user.id, room_id)
        if local_ban:
            raise UserBannedInRoom()

        existing_association = self.member_room_repo.get_association_by_ids(
            user.id, room_id
        )
        if existing_association:
            raise UserInRoomError()

        if room.is_private:
            if not password or not self.verify_room_password(room, password):
                raise InvalidRoomPasswordError()

        current_members_count = len(
            self.member_room_repo.get_members_by_room_id(room_id)
        )
        if current_members_count >= room.max_members:
            raise RoomPermissionDeniedError(
                detail="Комната заполнена. Невозможно присоединиться."
            )
        try:
            self.member_room_repo.add_member(user.id, room_id, role=Role.MEMBER.value)

            websocket_message_for_room = {
                "action": "join_room",
                "room_id": str(room.id),
                "user_id": str(user.id),
                "username": user.username,
                "detail": f"{user.username} присоединился к комнате",
            }
            websocket_message_for_user = {
                "action": "join_room",
                "room_id": str(room.id),
                "user_id": str(user.id),
                "username": user.username,
                "detail": f"Вы присоединились к комнате {room.name}",
            }
            await manager.send_personal_message(
                json.dumps(websocket_message_for_user), user.id
            )
            await manager.broadcast(room_id, json.dumps(websocket_message_for_room))

            return self.room_mapper.to_response(room)
        except Exception as e:

            raise ServerError(detail=f"Не удалось присоединиться к комнате. {e}")

    async def leave_room(self, room_id: uuid.UUID, user: UserEntity) -> dict[str, str]:
        """
        Пользователь покидает комнату.

        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты, которую покидает пользователь.
            user (User): Объект текущего пользователя.

        Returns:
            dict[str, Any]: Сообщение об успешном выходе.

        Raises:
            HTTPException: Если пользователь не является участником комнаты.
        """
        existing_association = self.member_room_repo.get_association_by_ids(
            user.id, room_id
        )
        if not existing_association:
            raise UserInRoomError(
                detail="Вы не являетесь участником этой комнаты.",
            )
        try:
            room_name_for_message = existing_association.room.name
            deleted_successfully = self.member_room_repo.remove_member(user.id, room_id)

            websocket_message_for_room = {
                "action": "leave_room",
                "room_id": str(room_id),
                "user_id": str(user.id),
                "username": user.username,
                "detail": f"{user.username} вышел из комнате",
            }
            websocket_message_for_user = {
                "action": "leave_room",
                "room_id": str(room_id),
                "user_id": str(user.id),
                "username": user.username,
                "detail": f"Вы вышли из комнате{room_name_for_message}",
            }
            await manager.send_personal_message(
                json.dumps(websocket_message_for_user), user.id
            )
            await manager.broadcast(room_id, json.dumps(websocket_message_for_room))

            if deleted_successfully:
                return {
                    "status": "success",
                    "detail": f"Вы успешно покинули комнату с ID: {room_id}.",
                    "user_id": str(user.id),
                    "room_id": str(room_id),
                }
        except Exception as e:
            raise ServerError(
                detail=f"Не удалось покинуть комнату.{e}",
            )

    async def get_room_members(self, room_id: uuid.UUID) -> list[UserResponse]:
        """
        Получает список участников комнаты.

        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты.

        Returns:
            List[UserResponse]: Список объектов UserResponse, являющихся участниками комнаты.

        Raises:
            HTTPException: Если комната не найдена.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        members = room.member_room
        if not members:
            return []

        return [self.user_mapper.to_response(member.user) for member in members]

    async def update_member_role(
        self,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: Role,
        current_user: UserEntity,
    ) -> RoomMemberResponse:
        """
        Изменяет роль члена комнаты. Только владелец комнаты может это делать.

        Args:
            self.db (Session): Сессия базы данных.
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
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        current_user_association = self.member_room_repo.get_association_by_ids(
            current_user.id, room_id
        )
        if (
            not current_user_association
            or current_user_association.role != Role.OWNER.value
        ):
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для изменения ролей в этой комнате. Только владелец может это делать.",
            )

        target_user_association = self.member_room_repo.get_association_by_ids(
            target_user_id, room_id
        )
        if not target_user_association:
            raise UserNotInRoomError(
                detail="Целевой пользователь не является членом этой комнаты.",
            )

        if target_user_id == current_user.id and new_role != Role.OWNER:
            raise OwnerRoleChangeError(
                detail="Владелец не может изменить свою собственную роль на не-владельца напрямую через этот метод.",
            )

        if target_user_id == room.owner_id and new_role != Role.OWNER:
            raise RoomPermissionDeniedError(
                detail="Нельзя разжаловать создателя комнаты.",
            )

        if target_user_association.role == new_role:
            raise RoleConflictError(
                detail="Пользователь уже имеет такую роль.",
            )

        try:
            updated_association = self.member_room_repo.update_role(
                room_id, target_user_id, new_role
            )

            if not updated_association:
                raise ServerError(
                    detail="Не удалось обновить роль члена комнаты.",
                )

            final_association_for_response = (
                self.member_room_repo.get_association_by_ids(target_user_id, room_id)
            )
            if not final_association_for_response:
                raise ServerError(
                    detail="Ошибка при формировании ответа после обновления роли.",
                )

            role_message_for_room = {
                "room_id": str(room_id),
                "username": target_user_association.user.username,
                "new_role": target_user_association.role,
                "moderator_id": str(current_user.id),
                "moderator_username": current_user.username,
                "detail": f"У пользователя {target_user_association.user.username} была обновлена роль до {target_user_association.role}",
            }
            role_message_for_user = {
                "room_id": str(room_id),
                "username": target_user_association.user.username,
                "new_role": target_user_association.role,
                "moderator_id": str(current_user.id),
                "moderator_username": current_user.username,
                "detail": f"У вас была обновлена роль до {new_role}",
            }
            await manager.send_personal_message(json.dumps(role_message_for_user))
            await manager.broadcast(room_id, json.dumps(role_message_for_room))

            return self.room_member_mapper.to_response(final_association_for_response)
        except Exception as e:
            raise ServerError(
                detail=f"Ошибка сервера при изменении роли: {e}",
            )

    async def kick_member_from_room(
        self, room_id: uuid.UUID, user_id: uuid.UUID, current_user: UserEntity
    ) -> dict[str, str]:
        """
        Удаляет указанного пользователя из комнаты. 🚪

        Эту операцию могут выполнять только владелец или модератор комнаты.
        Модераторы не могут кикать владельцев или других модераторов.
        Пользователь не может кикнуть самого себя.

        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
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
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        current_user_association = self.member_room_repo.get_association_by_ids(
            current_user.id, room_id
        )
        if not current_user_association or current_user_association.role not in [
            Role.OWNER.value,
            Role.MODERATOR.value,
        ]:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для изменения ролей в этой комнате. Только владелец и модератор может это делать.",
            )

        target_user_association = self.member_room_repo.get_association_by_ids(
            user_id, room_id
        )
        if not target_user_association:
            raise UserNotInRoomError(
                detail="Пользователь, которого вы пытаетесь кикнуть, не найден в этой комнате.",
            )
        if current_user.id == user_id:
            raise SelfInteractionError(detail="Нельзя кикнуть себя")
        if user_id == room.owner_id:
            raise RoomPermissionDeniedError(
                detail="Владельца нельяза кикнуть из комнаты.",
            )

        if current_user_association.role == Role.MODERATOR.value:
            if target_user_association.role == Role.MODERATOR.value:
                raise RoomPermissionDeniedError(detail="Нельзя кикнуть модератора")
            elif target_user_association.role == Role.OWNER.value:
                raise RoomPermissionDeniedError(detail="Нельзя кикнуть Владельца")

        try:
            kick_message_for_room = {
                "action": "you_weke_kicked",
                "kicked_user_id": user_id,
                "kicked_username": target_user_association.user.username,
                "room_id": room_id,
                "moderator_id": current_user.id,
                "detail": f"Пользователь {target_user_association.user.username} был кикнут из комнаты.",
            }
            kick_message_for_user = {
                "action": "user_kicked_from_room",
                "kicked_user_id": user_id,
                "kicked_username": target_user_association.user.username,
                "room_id": room_id,
                "moderator_id": current_user.id,
                "detail": f"Вы были кикнуты из комнаты {room.name}",
            }
            self.member_room_repo.remove_member(user_id, room_id)

            await manager.send_personal_message(
                json.dumps(kick_message_for_user), user_id
            )
            await manager.broadcast(room_id, json.dumps(kick_message_for_room))
            return {
                "action": "kick member",
                "status": "success",
                "user_id": user_id,
                "room_id": room_id,
            }
        except Exception as e:
            raise ServerError(
                detail=f"Ошибка сервера при кике пользователя: {e}",
            )

    async def ban_user_from_room(
        self,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        ban_data: BanCreate,
        current_user: UserEntity,
    ) -> BanResponse:
        """
        Банит пользователя в конкретной комнате или глобально.
        Только владелец комнаты может банить других пользователей.
        Модераторы НЕ могут банить.

        Args:
            self.db (Session): Сессия базы данных.
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
            room = self.room_repo.get_room_by_id(room_id)
            if not room:
                raise RoomNotFoundError()

            current_user_assoc = self.member_room_repo.get_association_by_ids(
                current_user.id, room_id
            )
            if not current_user_assoc or current_user_assoc.role != Role.OWNER.value:
                raise RoomPermissionDeniedError(
                    detail="У вас нет прав для бана пользователей в этой комнате. Только владелец может банить.",
                )

            if current_user.id == target_user_id:
                raise SelfInteractionError(
                    detail="Вы не можете забанить самого себя.",
                )

            existing_global_ban = self.ban_repo.is_user_banned_global(target_user_id)
            if existing_global_ban:
                raise UserBannedGlobal()

            existing_local_ban = self.ban_repo.is_user_banned_local(
                target_user_id, room_id
            )
            if existing_local_ban:
                raise UserBannedInRoom()

            existing_member_association = self.member_room_repo.get_association_by_ids(
                target_user_id, room_id
            )
            if existing_member_association:
                removed_from_room = self.member_room_repo.remove_member(
                    target_user_id, room_id
                )
                if not removed_from_room:
                    raise ServerError(
                        detail="Не удалось подготовить пользователя к бану.",
                    )

            new_ban_entry = self.ban_repo.add_ban(
                ban_user_id=target_user_id,
                room_id=room_id,
                reason=ban_data.reason,
                by_ban_user_id=current_user.id,
            )

            ban_notification_for_room = {
                "action": "ban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "banned_by": str(current_user.id),
                "reason": ban_data.reason if ban_data.reason else "не указана",
                "detail": f"Пользователь {target_user_id} был забанен в комнате.",
            }
            ban_notification_for_user = {
                "action": "ban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "banned_by": str(current_user.id),
                "reason": ban_data.reason if ban_data.reason else "не указана",
                "detail": f"Вы были забанены в комнате {room.name}.",
            }
            await manager.send_personal_message(
                json.dumps(ban_notification_for_user), target_user_id
            )
            await manager.broadcast(room_id, json.dumps(ban_notification_for_room))

            return self.ban_mapper.to_response(new_ban_entry)

        except Exception:
            raise ServerError(
                detail="Не удалось забанить пользователя из-за внутренней ошибки сервера.",
            )

    async def unban_user_from_room(
        self,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        current_user: UserEntity,
    ) -> dict[str, str]:
        """
        Снимает бан с пользователя в конкретной комнате.
        Только владелец комнаты может снимать баны.

        Args:
            self.db (Session): Сессия базы данных.
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
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()

        current_user_assoc = self.member_room_repo.get_association_by_ids(
            current_user.id, room_id
        )
        if not current_user_assoc or current_user_assoc.role != Role.OWNER.value:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для снятия банов в этой комнате. Только владелец может снимать баны.",
            )

        if current_user.id == target_user_id:
            raise SelfInteractionError(
                detail="Вы не можете снять бан с самого себя.",
            )

        existing_ban_to_unban = self.ban_repo.is_user_banned_local(
            target_user_id, room_id
        )
        if not existing_ban_to_unban:
            raise UserNotExistingBan(
                detail="Пользователь не забанен в этой комнате.",
            )
        try:
            unbanned_successfully = self.ban_repo.remove_ban_local(
                target_user_id, room_id
            )

            if not unbanned_successfully:
                raise ServerError(
                    detail="Не удалось снять бан из-за внутренней ошибки сервера.",
                )

            unban_notification_for_room = {
                "action": "unban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "unbanned_by": str(current_user.id),
                "detail": f"Бан пользователя {target_user_id} в комнате снят.",
            }
            unban_notification_for_user = {
                "action": "unban",
                "room_id": str(room_id),
                "user_id": str(target_user_id),
                "unbanned_by": str(current_user.id),
                "detail": f"Ваш бан в комнате{room.name} снят.",
            }
            await manager.send_personal_message(
                json.dumps(unban_notification_for_user), target_user_id
            )
            await manager.broadcast(room_id, json.dumps(unban_notification_for_room))

            return {
                "status": "success",
                "detail": f"Бан с пользователя {target_user_id} в комнате {room_id} успешно снят.",
            }
        except Exception:
            raise ServerError(
                detail="Не удалось снять бан из-за внутренней ошибки сервера.",
            )

    async def send_room_invite(
        self,
        room_id: uuid.UUID,
        inviter_id: uuid.UUID,
        invited_user_id: uuid.UUID,
    ) -> dict[str, str]:
        """
        Отправляет приглашение в комнату указанному пользователю.

        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
            room_id (uuid.UUID): ID комнаты, куда приглашают.
            inviter_id (uuid.UUID): ID пользователя, который отправляет приглашение.
            invited_user_id (uuid.UUID): ID пользователя, которого приглашают.

        Returns:
            dict[str, str]: Сообщение об успешной отправке приглашения.

        Raises:
            HTTPException: Если комната/пользователи не найдены, права недостаточны,
                           или приглашение невозможно отправить по другим причинам.
        """
        room = self.room_repo.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundError()
        inviter = self.user_repo.get_user_by_id(inviter_id)
        if not inviter:
            raise UserNotFound(
               detail="Приглашающий пользователь не найден"
            )

        invited = self.user_repo.get_user_by_id(invited_user_id)
        if not invited:
            raise UserNotFound(
                detail="Приглашаемый пользователь не найден"
            )

        if inviter_id == invited_user_id:
            raise SelfInteractionError(
                detail="Вы не можете пригласить самого себя в комнату."
            )

        inviter_membership = self.member_room_repo.get_member_room_association(
            room_id, inviter_id
        )
        if not inviter_membership or inviter_membership.role not in [
            Role.OWNER.value,
            Role.MODERATOR.value,
        ]:
            raise RoomPermissionDeniedError(
                detail="У вас нет прав для приглашения пользователей в эту комнату. Только владельцы и модераторы могут это делать.",
            )

        invited_member_in_room = self.member_room_repo.get_member_room_association(
            room_id, invited_user_id
        )
        if invited_member_in_room:
            raise UserInRoomError()

        have_banned = self.ban_repo.is_user_banned_local(invited_user_id, room_id)
        if have_banned:
            raise UserBannedInRoom()

        try:
            self.notify_repo.add_notification(
                invited_user_id,
                NotificationType.ROOM_INVITED,
                message=f"{inviter.username} приглашает вас в комнату {room.name}.",
                sender_id=inviter_id,
                room_id=room_id,
                related_object_id=room_id,
            )
            logger.info(
                f"RoomService: уведомление успешно отправлено пользователю {invited_user_id} из комнаты {room_id}"
            )
            ws_message = {
                "action": "room_invite_received",
                "room_id": str(room_id),
                "room_name": room.name,
                "inviter_id": str(inviter_id),
                "inviter_username": inviter.username,
                "detail": f"Вы получили приглашение в комнату {room.name} от {inviter.username}.",
            }
            await manager.send_personal_message(json.dumps(ws_message), invited_user_id)
            return {"status": "success", "detail": "Приглашение отправлено."}
        except Exception:
            logger.error(
                f"RoomService: Неизвестная ошибка при приглашении пользователя {invited_user_id} "
                f"в комнату {room_id}.",
                exc_info=True,
            )
            raise ServerError(
                detail="Не удалось создать уведомление из-за внутренней ошибки сервера.",
            )

    async def handle_room_invite_response(
        self,
        notification_id: uuid.UUID,
        current_user_id: uuid.UUID,
        action: NotificationType,
    ) -> NotificationResponse:
        """
        Обрабатывает ответ пользователя на приглашение в комнату (принять или отклонить).

        Args:
            self.db (Session): Сессия базы данных SQLAlchemy.
            notification_id (uuid.UUID): ID уведомления о приглашении.
            current_user_id (uuid.UUID): ID текущего пользователя, который отвечает на приглашение.
            action (str): Действие пользователя ("accept" для принятия, "decline" для отклонения).

        Returns:
            dict[str, str]: Сообщение о результате операции.

        Raises:
            HTTPException: Если уведомление не найдено, у пользователя нет прав,
                           уведомление не является приглашением, или возникла другая ошибка.
        """
        notification = self.notify_repo.get_notification_by_id(notification_id)
        if not notification:
            raise RoomNotFoundError()

        if not notification.user_id == current_user_id:
            raise NotificationNotPermission(
                detail="Это уведомление принадлежит не вам"
            )

        if not notification.notification_type != NotificationType.ROOM_INVITED.value:
            raise NotificationTypeError(
                detail="Это уведомление не является приглашением в комнату.",
            )

        if not notification.is_read:
            raise NotificationStateError(
                detail="Это приглашение уже было обработано."
            )

        room_id = notification.room_id
        inviter_id = notification.sender_id
        invited_user_id = notification.user_id

        try:
            room = self.room_repo.get_room_by_id(room_id)
            if not room:
                self.notify_repo.mark_notification_as_read(
                    notification_id, current_user_id
                )
                raise RoomNotFoundError(
                    detail="Комната, в которую вас пригласили, не найдена или удалена.",
                )

            inviter = self.user_repo.get_user_by_id(inviter_id) if inviter_id else None
            invited_user = self.user_repo.get_user_by_id(invited_user_id)

            if action == "accept":
                invited_member_in_room = (
                    self.member_room_repo.get_member_room_association(
                        room_id, invited_user_id
                    )
                )
                if invited_member_in_room:
                    self.notify_repo.mark_notification_as_read(
                        notification_id, current_user_id
                    )
                    raise UserInRoomError(
                        detail="Вы уже являетесь участником этой комнаты.",
                    )

                is_banned_local = self.ban_repo.is_user_banned_local(
                    invited_user_id, room_id
                )
                if is_banned_local:
                    self.notify_repo.mark_notification_as_read(
                        notification_id, current_user_id
                    )
                    raise UserBannedInRoom(
                        detail="Вы забанены в этой комнате и не можете присоединиться.",
                    )

                self.member_room_repo.add_member(invited_user_id, room_id, Role.MEMBER)

                self.notify_repo.mark_notification_as_read(
                    notification_id, current_user_id
                )

                websocket_message = {
                    "action": "user_joined_room",
                    "room_id": str(room_id),
                    "user_id": str(invited_user_id),
                    "username": invited_user.username,
                    "detail": f"{invited_user.username} присоединился(ась) к комнате.",
                }
                await manager.broadcast(room_id, json.dumps(websocket_message))

                if inviter:
                    self.notify_repo.add_notification(
                        user_id=inviter_id,
                        notification_type=NotificationType.SYSTEM_MESSAGE,
                        message=f"{invited_user.username} принял(а) ваше приглашение в комнату {room.name}.",
                        sender_id=invited_user_id,
                        room_id=room_id,
                        related_object_id=room_id,
                    )

                return {
                    "status": "success",
                    "detail": "Вы успешно присоединились к комнате.",
                }

            elif action == "decline":
                self.notify_repo.mark_notification_as_read(
                    notification_id, current_user_id
                )

                if inviter:
                    await self.notify_repo.add_notification(
                        user_id=inviter_id,
                        notification_type=NotificationType.SYSTEM_MESSAGE,
                        message=f"{invited_user.username} отклонил(а) ваше приглашение в комнату {room.name}.",
                        sender_id=invited_user_id,
                        room_id=room_id,
                        related_object_id=room_id,
                    )
                return {"status": "success", "detail": "Приглашение отклонено."}

            else:
                raise InvalidActionError(
                    detail='Недопустимое действие. Действие должно быть "accept" или "decline".',
                )
        except Exception:
            raise ServerError(
                detail="Не удалось обработать приглашение из-за внутренней ошибки сервера.",
            )

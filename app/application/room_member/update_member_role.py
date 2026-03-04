import uuid

from app.domain.entity import UserEntity
from app.domain.entity.member_room_association import MemberRoomEntity
from app.domain.interfaces.member_room_association import MemberRoomAssociationGateway
from app.domain.interfaces.room_gateway import RoomGateway
from app.domain.interfaces.user_gateway import UserGateway

from app.domain.enum import Role

from app.infrastructure.ws.manager_notify_service import NotifyService

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.room_exception import (
    RoomNotFoundError,
    UserNotInRoomError,
    RoomPermissionDeniedError,
    RoleConflictError,
    OwnerRoleChangeError,
)


class UpdateMemberRole:
    def __init__(
        self,
        room_repo: RoomGateway,
        user_repo: UserGateway,
        member_room_repo: MemberRoomAssociationGateway,
        notify_service: NotifyService
    ):
        self.room_repo = room_repo
        self.user_repo = user_repo
        self.member_room_repo = member_room_repo
        self.notify_service = notify_service
    
    async def update_member_role(
        self,
        room_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: Role,
        current_user: UserEntity,
    ) -> MemberRoomEntity:
        """
        Изменяет роль члена комнаты. Только владелец комнаты может это делать.
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

        target_user = self.user_repo.get_user_by_id(target_user_id)
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

            await self.notify_service.send_mesasge_for_user(
                room_id=str(room_id),
                username=target_user.username,
                new_role=target_user_association.role,
                moderator_id=str(current_user.id),
                moderator_username=current_user.username,
                detail=f"У вас была обновлена роль до {new_role}",
            )
            await self.notify_service.send_message_for_room(
                room_id=str(room_id),
                username=target_user.username,
                new_role=target_user_association.role,
                moderator_id=str(current_user.id),
                moderator_username=current_user.username,
                detail=f"У пользователя {target_user.username} была обновлена роль до {target_user_association.role}",
            )

            return final_association_for_response
        except Exception as e:
            raise ServerError(
                detail=f"Ошибка сервера при изменении роли: {e}",
            )
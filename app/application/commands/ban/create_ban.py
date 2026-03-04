from typing import Any
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.exceptions.ban_exception import UserBannedInRoom, UserBannedGlobal
from app.domain.exceptions.exception import ServerError
from app.domain.entity import UserEntity,BanEntity


class CreateBan:
    
    def __init__(self,ban_repo: BanGateway):
        self.ban_repo = ban_repo

    def add_ban(self,data_ban: dict[str,Any],current_user: UserEntity) -> BanEntity:
        """
        Добавляет новый бан для пользователя в комнате или глобально.
        Проверяет, не забанен ли пользователь уже
        """
        if data_ban.get('room_id'):
            existing_local_ban = self.ban_repo.is_user_banned_local( data_ban.get('ban_user_id'), data_ban.get('room_id'))
            if existing_local_ban:
                raise UserBannedInRoom()
            

        existing_global_ban = self.ban_repo.is_user_banned_global( data_ban.get('ban_user_id'))
        if existing_global_ban:
            raise UserBannedGlobal()

        try:
            new_ban_entry = self.ban_repo.add_ban(
                ban_user_id=data_ban.get('ban_user_id'),
                room_id=data_ban.get('room_id'),
                reason=data_ban.get('reason'),
                by_ban_user_id=current_user.id
            )

            return new_ban_entry
        except Exception:
            raise ServerError(
                detail="Не удалось добавить бан из-за внутренней ошибки сервера."
            )
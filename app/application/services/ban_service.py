import uuid
from typing import Any

from app.config.log_config import logger
from app.domain.interfaces.ban_gateway import BanGateway
from app.presentation.schemas.ban_schemas import BanResponse
from app.application.mappers.ban_mapper import BanMapper
from app.domain.exceptions.ban_exception import UserBannedInRoom, UserBannedGlobal, UserNotExistingBan
from app.domain.exceptions.exception import ServerError
from app.domain.entity import UserEntity


class BanService:
    """
    Реализует бизнес логику для работы с баном пользователей
    """

    def __init__(self,ban_repo: BanGateway,ban_mapper: BanMapper):
        self.ban_repo = ban_repo
        self.ban_mapper = ban_mapper

 
    def get_bans_by_admin(self,user_id: uuid.UUID) -> list[BanResponse]:
        """
        Получает список банов, выданных указанным пользователем (кто забанил).

        Args:
            user_id (uuid.UUID): ID пользователя, который выдал бан.

        Returns:
            List[BanResponse]: Список банов, выданных этим пользователем.
        """
        bans = self.ban_repo.get_bans_by_admin(user_id)
        if not bans:
            return []
        
        return [self.ban_mapper.to_response(ban) for ban in bans]

    
    def get_bans_on_user(self,user_id: uuid.UUID) -> list[BanResponse]:
        """
        Получает список банов, полученных указанным пользователем (кого забанили).

        Args:
            user_id (uuid.UUID): ID пользователя, который был забанен.

        Returns:
            List[BanResponse]: Список банов, полученных этим пользователем.
        """
        bans = self.ban_repo.get_bans_on_user(user_id)
        if not bans:
            return []
        
        return [self.ban_mapper.to_response(ban) for ban in bans]
    

    
    def add_ban(self,data_ban: dict[str,Any],current_user: UserEntity) -> BanResponse:
        """
        Добавляет новый бан для пользователя в комнате или глобально.
        Проверяет, не забанен ли пользователь уже.

        Args:
            data_ban: данные для бана (ID забаненного, room_id, причина).
            current_user (User): Текущий аутентифицированный пользователь, который выдает бан.

        Returns:
            BanResponse: Объект BanResponse, представляющий созданный бан.

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

            return self.ban_mapper.to_response(new_ban_entry)
        except Exception:
            raise ServerError(
                detail="Не удалось добавить бан из-за внутренней ошибки сервера."
            )
        
    
    def remove_ban(self, data_ban: dict[str,Any]) -> dict[str, str]:
        """
        Удаляет запись о бане пользователя.

        Args:
            data_ban :ID забаненного пользователя и room_id (опционально).

        Returns:
            dict[str, Any]: Словарь с сообщением об успешном снятии бана.

        """
        existing_ban_to_remove = None
        existing_ban_to_remove_local = None
        if data_ban.get('room_id'):
            existing_ban_to_remove_local = self.ban_repo.is_user_banned_local( data_ban.get('ban_user_id'), data_ban.get('room_id'))
            existing_ban_to_remove = True
        else:
            self.ban_repo.is_user_banned_global( data_ban.get('ban_user_id'))
        
        if not existing_ban_to_remove:
                logger.warning(f"BanService: Попытка снять несуществующий бан для user_id={data_ban.get('ban_user_id')}, room_id={data_ban.get('room_id')}")
                raise UserNotExistingBan()
        try:
            if existing_ban_to_remove_local:
                self.ban_repo.remove_ban_local(data_ban.get('room_id'),data_ban.get('ban_user_id'))
            else:
                self.ban_repo.remove_ban_global(data_ban.get('ban_user_id'))
            logger.info(f"BanService: Бан успешно снят для user_id={data_ban.get('ban_user_id')}, room_id={data_ban.get('room_id')}")
            
            return {
                "status": "success",
                "detail": "Бан успешно снят."
            }
        except Exception as e:
            logger.error(
                f"Внутренняя ошибка сервера при снятии бана. user_id: {data_ban.get('ban_user_id')}, "
                f"room_id: {data_ban.get('room_id') if data_ban.get('room_id') else 'глобальный'}. Ошибка: {e}",
                exc_info=True
            )
            raise ServerError(
                detail=f"Не удалось снять бан из-за внутренней ошибки сервера: {e}" 
            )
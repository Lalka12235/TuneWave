from typing import Any

from app.config.log_config import logger
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.exceptions.ban_exception import UserNotExistingBan
from app.domain.exceptions.exception import ServerError


class BanService:
    
    def __init__(self,ban_repo: BanGateway):
        self.ban_repo = ban_repo
    
    def remove_ban(self, data_ban: dict[str,Any]) -> dict[str, str]:
        """
        Удаляет запись о бане пользователя.
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
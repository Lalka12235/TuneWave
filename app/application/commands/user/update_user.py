from app.domain.interfaces.user_gateway import UserGateway
import uuid
from app.domain.entity import UserEntity

from app.config.log_config import logger
from typing import Any

class UpdateUser:
    
    def __init__(self,user_repo: UserGateway):
        self.user_repo = user_repo
    
    def update_user_profile(
        self, user_id: uuid.UUID, update_data: dict[str,Any]
    ) -> UserEntity:
        """
        Обновляет профиль пользователя.
        """
        updated_user = self.user_repo.update_user(user_id, update_data)
        logger.info(f"Профиль пользователя '{user_id}' успешно обновлен.")

        return updated_user

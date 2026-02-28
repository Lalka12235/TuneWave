from typing import Any
from app.domain.exceptions.user_exception import UserAlrediExist
from app.domain.interfaces.user_gateway import UserGateway
from app.domain.entity import UserEntity
from app.config.log_config import logger


class CreateUser:

    def __init__(self,user_repo: UserGateway):
        self.user_repo = user_repo
    
    def create_user(self, user_data: dict[str,Any]) -> UserEntity:
        """Создание пользователя"""
        user = self.user_repo.get_user_by_email(user_data.get('email'))

        if user:
            logger.warning("Попытка создать/обновить пользователя: уже существует.")
            raise UserAlrediExist(detail="Пользователь уже существует")
        
        new_user = self.user_repo.create_user(user_data)
        logger.info(
            f"Пользователь '{user_data.get('username')}' ({new_user.id}) успешно зарегистрирован."
        )
        return new_user
from app.repositories.user_repo import UserRepository
from backend.app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from fastapi import HTTPException, status

import logging

logger = logging.getLogger(__name__)

class UserServices:

    @staticmethod
    async def get_user(username: str):
        logger.debug(f'Попытка получить пользователя: {username}')
        user = await UserRepository.get_user(username)
        if user is None:
            logger.error(f'Пользователь не найден: {username}')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        logger.info(f'Пользователь найден: {username}')
        return {'message': 'User found', 'detail': username}

    @staticmethod
    async def register_user(user: UserRegisterSchema):
        logger.debug(f'Попытка регистрации пользователя: {user.username}')
        existing_user = await UserRepository.get_user(user.username)
        if existing_user:
            logger.error(f'Пользователь уже существует: {user.username}')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='User already exists'
            )
        user_id = await UserRepository.register_user(user)
        logger.info(f'Пользователь успешно зарегистрирован: {user.username}')
        return {'message': 'Account created', 'user_id': user_id}

    @staticmethod
    async def delete_user(user: UserLoginSchema):
        logger.debug(f'Попытка удаления пользователя: {user.username}')
        deleted_user = await UserRepository.delete_user(user)
        if not deleted_user:
            logger.error(f'Не удалось удалить пользователя: {user.username}')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found or incorrect password'
            )
        logger.info(f'Пользователь удалён: {user.username}')
        return {'message': 'Account deleted', 'user_id': deleted_user}

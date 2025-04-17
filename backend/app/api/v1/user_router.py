from fastapi import APIRouter,Depends
from app.services.user_services import UserServices
from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
import logging

logger = logging.getLogger(__name__)

from app.auth.auth import get_current_user,check_authorization


user = APIRouter(
    tags=['User']
)


@user.get('/users/{username}/get')
async def get_user(username: str):
    logger.info(f'Получение пользователя: {username}')
    return UserServices.get_user(username)



@user.post('/users/{username}/register')
async def register_user(user: UserRegisterSchema):
    logger.info(f'Регистарция пользователя: {user.username}')
    return UserServices.register_user(user)


@user.delete('/users/{username}/delete')
async def delete_account(user: UserLoginSchema,current_user: str = Depends(get_current_user), _ = Depends(check_authorization)):
    logger.warning(f'Удаление пользователя: {user.username}')
    return UserServices.delete_user(user)
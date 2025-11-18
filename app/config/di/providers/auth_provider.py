from dishka import Provider,provide,Scope

from app.application.mappers.user_mapper import UserMapper
from app.application.services.redis_service import RedisService
from app.domain.interfaces.ban_repo import BanRepository
from app.domain.interfaces.user_repo import UserRepository
from app.presentation.auth.auth import AuthService,get_current_user,get_current_user_id
from fastapi import Request

from app.domain.entity import UserEntity


class AuthProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def auth_service(
            self,
            user_repo: UserRepository,
            ban_repo: BanRepository,
            user_mapper: UserMapper,
            redis_service: RedisService,
    ) -> AuthService:
        return AuthService(user_repo, ban_repo, user_mapper, redis_service)

    @provide
    async def auth_data(self,request: Request) -> dict:
        data =  get_current_user_id(request)
        return data

    @provide
    async def current_user(self,auth_data: dict,user_repo: UserRepository) -> UserEntity:
        data = await get_current_user(auth_data,user_repo)
        return data
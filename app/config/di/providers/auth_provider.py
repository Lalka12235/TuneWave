from dishka import Provider,provide,Scope

from app.application.mappers.user_mapper import UserMapper
from app.application.services.redis_service import RedisService
from app.domain.entity import UserEntity
from app.domain.interfaces.ban_repo import BanRepository
from app.domain.interfaces.user_repo import UserRepository
from app.presentation.auth.auth import AuthService, get_current_user, get_current_user_id, AuthData


class AuthProvider(Provider):
    scope = Scope.REQUEST

    get_current_user = provide(get_current_user, provides=UserEntity)
    get_auth_data = provide(get_current_user_id, provides=AuthData, scope=Scope.REQUEST)

    @provide
    def auth_service(
            self,
            user_repo: UserRepository,
            ban_repo: BanRepository,
            user_mapper: UserMapper,
            redis_service: RedisService,
    ) -> AuthService:
        return AuthService(user_repo, ban_repo, user_mapper, redis_service)

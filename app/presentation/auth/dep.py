from app.infrastracture.db.repositories.user_repo import SQLalchemyUserRepository # Corrected import path
from app.infrastracture.db.repositories.ban_repo import SQLalchemyBanRepository # Corrected import path
from app.application.mappers.user_mapper import UserMapper # Corrected import path
from app.presentation.auth.auth import AuthService
from fastapi import Depends
from typing import Annotated

from app.infrastracture.db.repositories.dep import get_user_repo,get_ban_repo # Corrected import path
from app.application.mappers.mappers import get_user_mapper # Corrected import path
from app.application.services.redis_service import RedisService # Corrected import path
from app.application.dep import get_redis_service # Corrected import path


def get_auth_service(
        user_repo: Annotated[SQLalchemyUserRepository,Depends(get_user_repo)],
        ban_repo: Annotated[SQLalchemyBanRepository,Depends(get_ban_repo)],
        user_mapper: Annotated[UserMapper,Depends(get_user_mapper)],
        redis_service: Annotated[RedisService, Depends(get_redis_service)]
) -> AuthService:
    return AuthService(user_repo,ban_repo,user_mapper, redis_service)
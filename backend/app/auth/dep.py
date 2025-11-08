from app.repositories.user_repo import UserRepository
from app.repositories.ban_repo import BanRepository
from app.services.mappers.mappers import UserMapper
from app.auth.auth import AuthService
from fastapi import Depends
from typing import Annotated

from app.repositories.dep import get_user_repo,get_ban_repo
from app.services.mappers.mappers import get_user_mapper



def get_auth_service(
        user_repo: Annotated[UserRepository,Depends(get_user_repo)],
        ban_repo: Annotated[BanRepository,Depends(get_ban_repo)],
        user_mapper: Annotated[UserMapper,Depends(get_user_mapper)],
) -> AuthService:
    return AuthService(user_repo,ban_repo,user_mapper)
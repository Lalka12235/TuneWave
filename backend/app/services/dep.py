from app.repositories.dep import get_user_repo, get_ban_repo
from app.services.user_service import UserService
from app.services.ban_service import BanService
from typing import Annotated
from app.repositories.ban_repo import BanRepository
from app.repositories.user_repo import UserRepository
from fastapi import Depends


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    ban_repo: Annotated[BanRepository, Depends(get_ban_repo)],
):
    return UserService(user_repo, ban_repo)

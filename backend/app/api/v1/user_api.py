from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from typing import Annotated
from app.schemas.user_schemas import UserResponse
from app.services.user_service import UserService
from app.auth.auth import get_current_user
from app.config.session import get_db
from app.models.user import User


user = APIRouter(
    tags=['User']
)

@user.get('/me',response_model=UserResponse)
async def get_me(
    db: Annotated[Session,Depends(get_db)],
    user: Annotated[User,Depends(get_current_user)]
) -> UserResponse:
    """
    Получает профиль текущего аутентифицированного пользователя.
    
    Returns:
        UserResponse: Pydantic-модель с данными профиля пользователя.
    """
    return UserService._map_user_to_response(user)
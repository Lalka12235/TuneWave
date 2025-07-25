from app.utils.jwt import decode_access_token
from fastapi import HTTPException,status,Depends
from typing import Annotated
from app.services.user import UserService
from sqlalchemy.orm import Session
#from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
import uuid
from app.config.session import get_db
from app.models.user import User

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
oauth2_scheme = HTTPBearer(description="Введите ваш JWT-токен (Bearer <TOKEN>)")


def get_current_user_id(credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]) -> uuid.UUID:
    """
    Зависимость FastAPI, которая извлекает ID пользователя из JWT-токена.
    
    Args:
        token (str): JWT-токен, извлеченный из заголовка Authorization.
                     Предоставляется FastAPI благодаря OAuth2PasswordBearer.
                     
    Returns:
        uuid.UUID: ID пользователя, извлеченный из токена.
        
    Raises:
        HTTPException: Если токен недействителен, истек или не содержит ID пользователя.
    """
    token = credentials.credentials
    try: 
        data = decode_access_token(token)
        user_id = data.get('sub')

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail='Invalid user_id'
            )
        
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен: некорректный формат идентификатора пользователя."
        )

        return user_id

    except HTTPException as e:
        # Перехватываем HTTPException, выброшенные decode_access_token (истекший/недействительный токен)
        raise e # Перевыбрасываем их, чтобы FastAPI их обработал
    except Exception as e:
        # Общая обработка любых других неожиданных ошибок
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # 500 Internal Server Error для неожиданных ошибок
            detail=f"Не удалось проверить учетные данные: {e}"
        )


def get_current_user(
        db: Annotated[Session,Depends(get_db)],
        user_id:Annotated[uuid.UUID,Depends(get_current_user_id)]
) -> User:
    """
    Зависимость FastAPI, которая возвращает объект User для текущего аутентифицированного пользователя.
    
    Args:
        db (Session): Сессия базы данных (предоставляется get_db).
        user_id (uuid.UUID): ID пользователя (предоставляется get_current_user_id).
        
    Returns:
        User: Объект User из базы данных.
        
    Raises:
        HTTPException: Если пользователь не найден в БД или неактивен (401 Unauthorized).
    """
    user = UserService.get_user_by_id(db,user_id)

    return user


def login_user():
    pass
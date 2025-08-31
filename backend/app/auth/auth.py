from app.utils.jwt import decode_access_token
from fastapi import HTTPException,status,Depends
from typing import Annotated
from app.repositories.user_repo import UserRepository
from sqlalchemy.orm import Session
#from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
import uuid
from app.config.session import get_db
from app.models.user import User
from app.logger.log_config import logger

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
            logger.warning("JWT-токен не содержит идентификатор пользователя (поле 'sub').")
            raise HTTPException(
                status_code=401,
                detail='Invalid user_id'
            )
        
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Недействительный JWT-токен: 'sub' поле '{user_id}' не является валидным UUID.")
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен: некорректный формат идентификатора пользователя."
        )

        return user_id

    except HTTPException as e:
        logger.warning(f"Ошибка аутентификации JWT: {e.detail}")
        # Перехватываем HTTPException, выброшенные decode_access_token (истекший/недействительный токен)
        raise e # Перевыбрасываем их, чтобы FastAPI их обработал
    except Exception as e:
        # Общая обработка любых других неожиданных ошибок
        logger.error(f'Не удалось проверить учетные данные JWT: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # 500 Internal Server Error для неожиданных ошибок
            detail="Не удалось проверить учетные данные"
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
    user = UserRepository.get_user_by_id(db, user_id)

    if not user:
        logger.warning(f"Пользователь с ID {user_id} не найден в базе данных или неактивен.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или неактивен."
        )
    return user
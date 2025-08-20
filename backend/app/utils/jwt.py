import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from app.config.settings import settings
from fastapi import HTTPException, status 
from datetime import datetime, timedelta, timezone
from app.logger.log_config import logging


def create_access_token(
    payload: dict, 
    expires_delta: timedelta | None = None 
) -> str:
    """
    Создает JWT (JSON Web Token) для аутентификации пользователя.

    Args:
        payload (dict): Данные, которые будут закодированы в токен (например, {'sub': user_id}).
        expires_delta (timedelta | None): Время жизни токена. Если None, используется значение из настроек.

    Returns:
        str: Закодированная строка JWT.
    """
    to_encode = payload.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    

    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Декодирует и проверяет JWT (JSON Web Token).

    Args:
        token (str): Строка JWT для декодирования.

    Returns:
        dict: Декодированный payload токена.

    Raises:
        HTTPException: Если токен недействителен (истек, некорректная подпись и т.д.).
    """
    try:
        decoded_payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return decoded_payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logging.error(f'Could not validate credentials: {e}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials"
        )
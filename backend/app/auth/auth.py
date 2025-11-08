from app.auth.jwt import decode_access_token
from fastapi import Depends
from typing import Annotated
from app.repositories.user_repo import UserRepository
from app.repositories.ban_repo import BanRepository
from app.services.mappers.mappers import UserMapper
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
import uuid
from app.schemas.entity import UserEntity
from app.logger.log_config import logger
from app.auth.jwt import create_access_token, decode_access_token
from app.schemas.user_schemas import (
    GoogleOAuthData,
    SpotifyOAuthData,
    Token,
    UserResponse
)
from jwt import exceptions
from infrastructure.celery.tasks import send_email_task

from app.exceptions.user_exception import (
    UserNotAuthorized,
) 
from app.exceptions.exception import ServerError
from app.exceptions.auth_exception import (
    InvalidTokenError,
    TokenDecodeError,
    UserBannedError,
)
from app.exceptions.user_exception import UserNotFound
from app.config.settings import settings


oauth2_scheme = HTTPBearer(description="Введите ваш JWT-токен (Bearer <TOKEN>)")


class AuthService:

    def __init__(self,user_repo: UserRepository,ban_repo: BanRepository,user_mapper: UserMapper):
        self.user_repo = user_repo
        self.ban_repo = ban_repo
        self.user_mapper = user_mapper


    def _check_existing_user_by_email(self,email: str) -> User:
        """
        Проверяет существование пользователя по почте
        """
        user = self.user_repo.get_user_by_email(email)
        if not user:
            logger.warning(f"Пользователь не найден {email}")
        return user

    def _check_global_bal_user(self,user_id: uuid.UUID) -> bool:
        """
        Проверка пользователя на наличие бана на платформе
        """
        global_ban = self.ban_repo.is_user_banned_global(user_id)
        if global_ban:
            logger.warning(
                f"Попытка входа забаненного пользователя Google: ID '{user_id}'."
            )
            raise UserBannedError(
                detail="Ваш аккаунт заблокирован. Свяжитесь с поддержкой для получения дополнительной информации.",
            )
        return global_ban

            
    async def authenticate_user_with_google(
        self, google_data: GoogleOAuthData
    ) -> tuple[UserResponse, Token]:
        """
        Аутентифицирует пользователя через Google OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """

        user = self._check_existing_user_by_email(google_data.email)
        if not user:
            user = self.user_repo.get_user_by_google_id(google_data.google_id)
        

        if user:
            self._check_global_bal_user(user.id)
            update_data = {
                "google_access_token": google_data.google_access_token,
                "google_token_expires_at": google_data.google_token_expires_at,
            }

            if google_data.google_refresh_token:
                update_data["google_refresh_token"] = google_data.google_refresh_token

            if not user.google_id:
                update_data["google_id"] = google_data.google_id
                update_data["google_image_url"] = google_data.google_image_url
            if google_data.is_email_verified and not user.is_email_verified:
                update_data["is_email_verified"] = True
            try:
                user = self.user_repo.update_user(user, update_data)
                logger.info(
                    f"Пользователь '{user.id}' успешно обновлен через Google OAuth."
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при обновлении пользователя '{user.id}' через Google OAuth: {e}",
                    exc_info=True,
                )
                raise ServerError(
                    detail="Ошибка при обновлении пользователя",
                )
        else:
            user_data = {
                "username": google_data.username,
                "email": google_data.email,
                "is_email_verified": google_data.is_email_verified,
                "google_id": google_data.google_id,
                "google_image_url": google_data.google_image_url,
                "google_access_token": google_data.google_access_token,
                "google_refresh_token": google_data.google_refresh_token,
                "google_token_expires_at": google_data.google_token_expires_at,
            }
            try:
                user = self.user_repo.create_user(user_data)
                logger.info(
                    f"Новый пользователь '{user.id}' зарегистрирован через Google OAuth."
                )
                send_email_task.delay(google_data.email,google_data.username)
            except Exception as e:
                logger.error(
                    f"Ошибка при создании пользователя через Google OAuth '{google_data.email}': {e}",
                    exc_info=True,
                )
                raise ServerError(
                    detail="Ошибка при создании пользователя",
                )

            from datetime import timedelta

            access_token = create_access_token(
                payload={"sub": str(user.id)},
                expires_delta=timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            return self.user_mapper.to_response(user), Token(
                access_token=access_token, token_type="bearer"
            )

    async def authenticate_user_with_spotify(
            self, spotify_data: SpotifyOAuthData
        ) -> tuple[UserResponse, Token]:
        """
        Аутентифицирует пользователя через Spotify OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """
        user = self.user_repo.get_user_by_email(spotify_data.email)
        if not user:
            logger.warning(f"Пользователь не найден {spotify_data.email}")
            user = self.user_repo.get_user_by_spotify_id(spotify_data.spotify_id)

        if user:
            self._check_global_bal_user(user.id)
            update_data = {}
            if not user.spotify_id:
                update_data["spotify_id"] = spotify_data.spotify_id
                update_data["spotify_image_url"] = spotify_data.spotify_image_url
                update_data["spotify_profile_url"] = spotify_data.spotify_profile_url

            update_data["spotify_access_token"] = spotify_data.spotify_access_token
            update_data["spotify_refresh_token"] = spotify_data.spotify_refresh_token
            update_data["spotify_token_expires_at"] = (
                spotify_data.spotify_token_expires_at
            )
            update_data["spotify_scope"] = spotify_data.spotify_scope

            try:
                if update_data:
                    user = self.user_repo.update_user(user, update_data)
                    logger.info(
                        f"Пользователь '{user.id}' успешно обновлен через Spotify OAuth."
                    )
            except Exception as e:
                logger.error(
                    f"Ошибка при обновлении пользователя '{user.id}' через Spotify OAuth: {e}",
                    exc_info=True,
                )
                raise ServerError(
                    detail="Ошибка при создании пользователя",
                )

        else:
            user_data = {
                "username": spotify_data.username,
                "email": spotify_data.email,
                "is_email_verified": False,
                "spotify_id": spotify_data.spotify_id,
                "spotify_profile_url": spotify_data.spotify_profile_url,
                "spotify_image_url": spotify_data.spotify_image_url,
                "spotify_access_token": spotify_data.spotify_access_token,
                "spotify_refresh_token": spotify_data.spotify_refresh_token,
                "spotify_token_expires_at": spotify_data.spotify_token_expires_at,
                "spotify_scope": spotify_data.spotify_scope,
            }

            try:
                user = self.user_repo.create_user(user_data)
                logger.info(
                    f"Новый пользователь '{user.id}' зарегистрирован через Spotify OAuth."
                )
                send_email_task.delay(spotify_data.email,spotify_data.username)
            except Exception as e:
                logger.error(
                    f"Ошибка при создании пользователя через Spotify OAuth '{spotify_data.email}': {e}",
                    exc_info=True,
                )
                raise ServerError(
                    detail="Ошибка при создании пользователя",
                )

        from datetime import timedelta

        access_token = create_access_token(
            payload={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return self.user_mapper.to_response(user), Token(
            access_token=access_token, token_type="bearer"
        )

def get_user_by_token(token: str) -> UserEntity:
        """_summary_
        Args:
            db (Session): _description_
            token (str): _description_
        Returns:
            User: _description_
        """
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                logger.warning(
                    "Ошибка декодирования токена: отсутствует 'sub' (ID пользователя)."
                )
                raise UserNotAuthorized(
                    detail="Невалидный токен: отсутствует ID пользователя",
                )
            user = UserRepository.get_user_by_id(user_id)
            return user
        except exceptions.DecodeError:
            logger.warning("Невалидный JWT-токен: ошибка декодирования.")
            raise TokenDecodeError()
        
    
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
            raise InvalidTokenError()
        
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Недействительный JWT-токен: 'sub' поле '{user_id}' не является валидным UUID.")
            raise InvalidTokenError(detail="Недействительный токен: некорректный формат идентификатора пользователя.")
        return user_id
    except exceptions.DecodeError:
        raise TokenDecodeError()
    except Exception as e:
        logger.error(f'Ошибка проверки JWT: {e}', exc_info=True)
        raise TokenDecodeError("Ошибка проверки токена")
    
    
def get_current_user(
        user_id:Annotated[uuid.UUID,Depends(get_current_user_id)]
) -> UserEntity:
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
    user = UserRepository.get_user_by_id(user_id)
    if not user:
        logger.warning(f"Пользователь с ID {user_id} не найден в базе данных или неактивен.")
        raise UserNotFound()
    return user
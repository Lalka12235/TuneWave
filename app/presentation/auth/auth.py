from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.interfaces.user_gateway import UserGateway
from app.application.mappers.mappers import UserMapper
from fastapi.security import HTTPBearer
import uuid
from app.domain.entity.user import UserEntity
from app.config.log_config import logger
from app.presentation.schemas.user_schemas import (
    GoogleOAuthData,
    SpotifyOAuthData,
    Token,
    UserResponse,
)
from app.infrastructure.celery.tasks import send_email_task
from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.auth_exception import (
    UserBannedError,
)
from app.application.services.redis_service import RedisService
from app.application.services.session_service import SessionID, SessionService
from app.config.settings import settings

oauth2_scheme = HTTPBearer(description="Введите ваш JWT-токен (Bearer <TOKEN>)")


class AuthService:

    def __init__(
        self,
        user_repo: UserGateway,
        ban_repo: BanGateway,
        user_mapper: UserMapper,
        redis_service: RedisService,
        session_service: SessionService,
    ):
        self.user_repo = user_repo
        self.ban_repo = ban_repo
        self.user_mapper = user_mapper
        self.redis_service = redis_service
        self.session_service = session_service

    def _check_existing_user_by_email(self, email: str) -> UserEntity:
        """
        Проверяет существование пользователя по почте
        """
        user = self.user_repo.get_user_by_email(email)
        if not user:
            logger.warning(f"Пользователь не найден {email}")
        return user

    def _check_global_bal_user(self, user_id: uuid.UUID) -> bool:
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
    
    async def _save_token_and_session_spotify(self,user_id: uuid.UUID,spotify_data: SpotifyOAuthData) -> SessionID | None:
        key_access = f"spotify_auth:{user_id}:access"
        key_config = f"spotify_auth:{user_id}:config"

        hset_dict = {
            "refresh_token": spotify_data.spotify_access_token,
            "expires_at": str(spotify_data.spotify_token_expires_at),
        }

        session_id = self.session_service.generate_session_id()
        key_session = f"session:{session_id}"

        save_session_id = await self.redis_service.set(
            key_session, user_id, settings.SESSION_EXPIRATION
        )

        save_access_token = await self.redis_service.set(
            key_access,
            spotify_data.spotify_access_token,
            spotify_data.spotify_token_expires_at,
        )
        save_refresh_token = await self.redis_service.hset(key_config, hset_dict)

        if not save_access_token and not save_refresh_token and save_session_id:
            return None
        return session_id

    async def _save_token_and_session_google(
        self,
        user_id: uuid.UUID,
        google_data: GoogleOAuthData,
    ) -> SessionID | None:
        key_access = f"google_auth:{user_id}:access"
        key_config = f"google_auth:{user_id}:config"
        session_id = self.session_service.generate_session_id()
        key_session = f"session:{session_id}"

        hset_dict = {
            "refresh_token": google_data.google_refresh_token,
            "expires_at": str(google_data.google_token_expires_at),
        }

        save_session_id = await self.redis_service.set(
            key_session, user_id, settings.SESSION_EXPIRATION
        )

        save_access_token = await self.redis_service.set(
            key_access,
            google_data.google_access_token,
            google_data.google_token_expires_at,
        )
        save_refresh_token = await self.redis_service.hset(key_config, hset_dict)

        if not save_access_token and not save_refresh_token and save_session_id:
            return False
        return session_id
   

    async def authenticate_user_with_google(
        self, google_data: GoogleOAuthData
    ) -> tuple[UserResponse, SessionID] | None:
        """
        Аутентифицирует пользователя через Google OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """

        user = self._check_existing_user_by_email(google_data.email)

        if user:
            self._check_global_bal_user(user.id)
            update_data = {}
            
            session_id = self._save_token_and_session_google(user.id,google_data)
            if session_id is None:
                raise ServerError(
                    detail="Ошибка при сохранение токенов и создании сессии. Попробуй заново авторизоваться"
                )

            if not user.google_id:
                update_data["google_id"] = google_data.google_id
                update_data["google_image_url"] = google_data.google_image_url
            if google_data.is_email_verified and not user.is_email_verified:
                update_data["is_email_verified"] = True
            
            if update_data:
                user = self.user_repo.update_user(user, update_data)
                logger.info(
                    f"Пользователь '{user.id}' успешно обновлен через Google OAuth."
                )
        else:
            user_data = {
                "username": google_data.username,
                "email": google_data.email,
                "is_email_verified": google_data.is_email_verified,
                "google_id": google_data.google_id,
                "google_image_url": google_data.google_image_url,
            }
            
            user = self.user_repo.create_user(user_data)
            logger.info(
                f"Новый пользователь '{user.id}' зарегистрирован через Google OAuth."
            )
            send_email_task.delay(google_data.email, google_data.username)

            return self.user_mapper.to_response(user), session_id

    async def authenticate_user_with_spotify(
        self, spotify_data: SpotifyOAuthData
    ) -> tuple[UserResponse, SessionID]:
        """
        Аутентифицирует пользователя через Spotify OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """
        user = self.user_repo.get_user_by_email(spotify_data.email)
        
        if user:
            self._check_global_bal_user(user.id)
            update_data = {}

            session_id = self._save_token_and_session_spotify(user.id,spotify_data)
            if session_id is None:
                raise ServerError(
                    detail="Ошибка при сохранение токенов и создании сессии. Попробуй заново авторизоваться"
                )

            if not user.spotify_id:
                update_data["spotify_id"] = spotify_data.spotify_id
                update_data["spotify_image_url"] = spotify_data.spotify_image_url
                update_data["spotify_profile_url"] = spotify_data.spotify_profile_url
            #update_data["spotify_scope"] = spotify_data.spotify_scope

            if update_data:
                user = self.user_repo.update_user(user, update_data)
                logger.info(
                    f"Пользователь '{user.id}' успешно обновлен через Spotify OAuth."
                )
        else:
            user_data = {
                "username": spotify_data.username,
                "email": spotify_data.email,
                "is_email_verified": False,
                "spotify_id": spotify_data.spotify_id,
                "spotify_profile_url": spotify_data.spotify_profile_url,
                "spotify_image_url": spotify_data.spotify_image_url,
                "spotify_scope": spotify_data.spotify_scope,
            }
            
            user = self.user_repo.create_user(user_data)
            logger.info(
                f"Новый пользователь '{user.id}' зарегистрирован через Spotify OAuth."
            )
            send_email_task.delay(spotify_data.email, spotify_data.username)

        return self.user_mapper.to_response(user), session_id
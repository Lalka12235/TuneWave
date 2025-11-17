from app.infrastructure.db.repositories.user_repo import SQLalchemyUserRepository
from app.presentation.auth.jwt import decode_access_token
from fastapi import Depends
from typing import Annotated
from app.domain.interfaces.ban_repo import BanRepository
from app.domain.interfaces.user_repo import UserRepository 
from app.application.mappers.mappers import UserMapper 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
import uuid
from app.domain.entity.user import UserEntity
from app.config.log_config import logger
from app.presentation.schemas.user_schemas import (
    GoogleOAuthData,
    SpotifyOAuthData,
    Token,
    UserResponse
)
from app.infrastructure.celery.tasks import send_email_task
from jwt import exceptions
from app.infrastructure.db.repositories.dep import get_user_repo

from app.domain.exceptions.exception import ServerError
from app.domain.exceptions.auth_exception import ( 
    InvalidTokenError,
    TokenDecodeError,
    UserBannedError,
)
from app.domain.exceptions.user_exception import UserNotFound,UserNotAuthorized 
from app.application.services.redis_service import RedisService
import httpx


oauth2_scheme = HTTPBearer(description="Введите ваш JWT-токен (Bearer <TOKEN>)")


class AuthService:

    def __init__(self,user_repo: UserRepository,ban_repo: BanRepository,user_mapper: UserMapper,redis_service: RedisService):
        self.user_repo = user_repo
        self.ban_repo = ban_repo
        self.user_mapper = user_mapper
        self.redis_service = redis_service


    def _check_existing_user_by_email(self,email: str) -> UserEntity:
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
            update_data = {}

            key_access = f'google_auth:{user.id}:access'
            key_config = f'google_auth:{user.id}:config'

            hset_dict = {
                'refresh_token':google_data.google_refresh_token,
                'expires_at':str(google_data.google_token_expires_at),
            }

            save_access_token = await self.redis_service.set(key_access,google_data.google_access_token,google_data.google_token_expires_at)
            save_refresh_token = await self.redis_service.hset(key_config,hset_dict)

            if not save_access_token and not save_refresh_token:
                raise ServerError(
                    detail='Ошибка при сохранение токенов. Попробуй заново авторизоваться'
                )
            
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

            return self.user_mapper.to_response(user), Token(
                access_token=google_data.google_access_token, token_type="bearer"
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

            key_access = f'spotify_auth:{user.id}:access'
            key_config = f'spotify_auth:{user.id}:config'
            
            hset_dict = {
                'refresh_token': spotify_data.spotify_access_token,
                'expires_at': str(spotify_data.spotify_token_expires_at),
            }

            save_access_token = await self.redis_service.set(key_access,spotify_data.spotify_access_token,spotify_data.spotify_token_expires_at)
            save_refresh_token = await self.redis_service.hset(key_config   ,hset_dict)

            if not save_access_token and not save_refresh_token:
                raise ServerError(
                    detail='Ошибка при сохранение токенов. Попробуй заново авторизоваться'
                )
            
            if not user.spotify_id:
                update_data["spotify_id"] = spotify_data.spotify_id
                update_data["spotify_image_url"] = spotify_data.spotify_image_url
                update_data["spotify_profile_url"] = spotify_data.spotify_profile_url
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

        return self.user_mapper.to_response(user), Token(
            access_token=spotify_data.spotify_access_token, token_type="bearer"
        )


async def check_provider(token: str) -> dict[str, str]:
    google_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    spotify_url = "https://api.spotify.com/v1/me"

    async with httpx.AsyncClient() as client:

        google_resp = await client.get(
            google_url,
            headers={"Authorization": f"Bearer {token}"}
        )

        if google_resp.status_code == 200:
            data = google_resp.json()
            return {
                "provider": "google",
                "external_id": data["sub"],
            }

        spotify_resp = await client.get(
            spotify_url,
            headers={"Authorization": f"Bearer {token}"}
        )

        if spotify_resp.status_code == 200:
            data = spotify_resp.json()
            return {
                "provider": "spotify",
                "external_id": data["id"],
            }

        raise InvalidTokenError("Invalid access token (not Google or Spotify).")


async def get_current_user_id(credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]) -> dict[str,str]:
    token = credentials.credentials
    provider_data = await check_provider(token)

    return provider_data


async def get_current_user(
        auth_data: Annotated[dict, Depends(get_current_user_id)],
        user_repo: Annotated[SQLalchemyUserRepository, Depends(get_user_repo)]
) -> UserEntity:
    provider = auth_data["provider"]
    external_id = auth_data["external_id"]

    if provider == "google":
        user = user_repo.get_user_by_google_id(external_id)

    elif provider == "spotify":
        user = user_repo.get_user_by_spotify_id(external_id)

    else:
        raise UserNotAuthorized()

    if not user:
        raise UserNotFound()

    return user
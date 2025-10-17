from fastapi import HTTPException,status, UploadFile
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.schemas.user_schemas import UserResponse, UserCreate, UserUpdate,Token,GoogleOAuthData, SpotifyOAuthData
import uuid
from typing import Any
from app.config.settings import settings
from app.utils.jwt import decode_access_token
from jwt import exceptions
from infrastructure.celery.tasks import send_email_task
import os
from app.repositories.ban_repo import BanRepository
from app.logger.log_config import logger

class UserService:

    def __init__(self,user_repo: UserRepository):
        self.user_repo = user_repo
        
        
    def _check_for_existing_user_and_raise_if_found(
        self,
        email: str | None = None,
        google_id: str | None = None,
        spotify_id: str | None = None,
        exclude_user_id: uuid.UUID | None = None
    ):
        """
        Вспомогательный метод для проверки существования пользователя по различным идентификаторам.
        Если пользователь найден (и его ID не совпадает с exclude_user_id), выбрасывает HTTPException (409 Conflict).
        """
        if email:
            user = self.user_repo.get_user_by_email(email)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                logger.warning(f"Попытка создать/обновить пользователя: email '{email}' уже существует.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Пользователь с email '{email}' уже существует."
                )
        
        if google_id:
            user = self.user_repo.get_user_by_google_id(google_id)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                logger.warning(f"Попытка создать/обновить пользователя: Google ID '{google_id}' уже существует.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Пользователь с Google ID '{google_id}' уже существует."
                )
        
        if spotify_id:
            user = self.user_repo.get_user_by_spotify_id( spotify_id)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                logger.warning(f"Попытка создать/обновить пользователя: Spotify ID '{spotify_id}' уже существует.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Пользователь с Spotify ID '{spotify_id}' уже существует."
                )


    
    def _map_user_to_response(user: User) -> UserResponse:
        """
        Вспомогательный метод для преобразования объекта User SQLAlchemy в Pydantic UserResponse.
        Это централизованное место для форматирования данных, возвращаемых клиенту.
        """
        # Pydantic's model_validate() автоматически преобразует SQLAlchemy ORM-объект
        # в Pydantic-модель, благодаря Config.from_attributes = True в UserResponse.
        return UserResponse.model_validate(user)


    
    async def get_user_by_id(self,user_id: uuid.UUID) -> dict[str,Any]:
        """
        Получает пользователя по его уникальному ID.
        
        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): Уникальный идентификатор пользователя.
            
        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).
            
        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Запрос пользователя по ID: Пользователь '{user_id}' не найден.")
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    
    
    def get_user_by_email(self,email: str) -> UserResponse:
        """
        Получает пользователя по его email.
        
        Args:
            db (Session): Сессия базы данных.
            email (str): Email пользователя.
            
        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).
            
        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_email(email)
        if not user:
            logger.warning(f"Запрос пользователя по email: Пользователь с email '{email}' не найден.")
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    

    
    def get_user_by_spotify_id(self, spotify_id: str) -> UserResponse:
        """
        Получает пользователя по его Spotify ID.
        
        Args:
            db (Session): Сессия базы данных.
            spotify_id (str): Spotify ID пользователя.
            
        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).
            
        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_spotify_id(spotify_id)
        if not user:
            logger.warning(f"Запрос пользователя по Spotify ID: Пользователь с Spotify ID '{spotify_id}' не найден.")
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    
    
    
    def get_user_by_google_id(self,google_id: str) -> UserResponse:
        """
        Получает пользователя по его Google ID.
        
        Args:
            db (Session): Сессия базы данных.
            google_id (str): Google ID пользователя.
            
        Raises:
            HTTPException: Если пользователь не найден (статус 404 NOT FOUND).
            
        Returns:
            UserResponse: Pydantic-модель с данными пользователя.
        """
        user = self.user_repo.get_user_by_google_id(google_id)
        if not user:
            logger.warning(f"Запрос пользователя по Google ID: Пользователь с Google ID '{google_id}' не найден.")
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    


    
    async def create_user(self,user_data: UserCreate) -> UserResponse:
        """Создание пользователя

        Args:
            db (Session): Сессия базы данных.
            user_data (UserCreate): Данные для создания пользоателя

        Returns:
            UserResponse: Информация о создании
        """
        UserService._check_for_existing_user_and_raise_if_found(
            
            user_data.email,
            user_data.google_id,
            user_data.spotify_id
        )
        try:
            new_user = self.user_repo.create_user(user_data.model_dump())
            logger.info(f"Пользователь '{user_data.username}' ({new_user.id}) успешно зарегистрирован.")
            subject = "Добро пожаловать в TuneWave!"
            body = f"""
            Привет, {user_data.username}!

            Спасибо за регистрацию в TuneWave. Мы рады видеть тебя в нашем музыкальном сообществе.
            Начни создавать комнаты и делиться музыкой с друзьями!

            С уважением,
            Команда TuneWave
            """
            email_sent = (user_data.email, subject, body)
            if not email_sent:
                logger.warning(f'Сообщение на почту не отправилось {email_sent}')
                pass
        except Exception as e:
            self.user_repo.db.rollback()
            logger.error(f"Ошибка при создании пользователя '{user_data.email}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании пользователя"
            )
        

        return UserService._map_user_to_response(new_user)
    
    
    async def update_user_profile(self, user_id: uuid.UUID, update_data: UserUpdate) -> UserResponse:
        """
        Обновляет профиль пользователя.
        Включает проверку на уникальность email, если он изменяется.
        
        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, чей профиль обновляется.
            update_data (UserUpdate): Pydantic-модель с данными для обновления.
            
        Returns:
            UserResponse: Обновленный объект UserResponse.
            
        Raises:
            HTTPException: Если пользователь не найден (404) или новый email уже занят другим пользователем (409).
        """
        user = self.user_repo.get_user_by_id( user_id)
        if not user:
            logger.warning(f"Попытка обновить профиль несуществующего пользователя с ID '{user_id}'.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден."
            )
        
        data_to_update = update_data.model_dump(exclude_unset=True) 
        try:
            updated_user = self.user_repo.update_user( user, data_to_update)
            logger.info(f"Профиль пользователя '{user_id}' успешно обновлен.")
        except Exception as e:
            self.user_repo.db.rollback()
            logger.error(f"Ошибка при обновлении профиля пользователя '{user_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обновлении пользователя"
            )

        return UserService._map_user_to_response(updated_user)
    

    
    def hard_delete_user(self,user_id: uuid.UUID) -> dict[str,Any]:
        """_summary_

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя для физического удаления.

        Raises:
            HTTPException: Пользователь не найден(404)

        Returns:
            dict[str,Any]: Информация об удалении
        """
        user = self.user_repo.get_user_by_id(user_id)

        if not user:
            logger.warning(f"Попытка удалить несуществующего пользователя с ID '{user_id}'.")
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        try:
            self.user_repo.hard_delete_user(user_id)
        except Exception as e:
            self.user_repo.db.rollback()
            logger.error(f"Ошибка при физическом удалении пользователя '{user_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при удаление пользователя"
            )

        return {
            'detail': 'delete user',
            'status': 'success',
            'id': user_id,
        }
    

    
    async def authenticate_user_with_google(self, google_data: GoogleOAuthData) -> tuple[UserResponse, Token]:
        """
        Аутентифицирует пользователя через Google OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """

        user = self.user_repo.get_user_by_email( google_data.email)
        if not user:
            logger.warning(f'Пользователь не найден {google_data.email}')
            user = self.user_repo.get_user_by_google_id( google_data.google_id)

        

        if user:
            global_ban = BanRepository.is_user_banned_global(user.id)
            if global_ban:
                logger.warning(f"Попытка входа забаненного пользователя Google: ID '{user.id}'.")
                raise HTTPException(
                    status_code=403,
                    detail="Ваш аккаунт заблокирован. Свяжитесь с поддержкой для получения дополнительной информации."
                )
            update_data = {
                'google_access_token': google_data.google_access_token,
                'google_token_expires_at': google_data.google_token_expires_at
            }
            
            if google_data.google_refresh_token:
                update_data['google_refresh_token'] = google_data.google_refresh_token

            if not user.google_id:
                update_data['google_id'] = google_data.google_id
                update_data['google_image_url'] = google_data.google_image_url
            if google_data.is_email_verified and not user.is_email_verified:
                update_data['is_email_verified'] = True
            try:
                user = self.user_repo.update_user( user, update_data)
                logger.info(f"Пользователь '{user.id}' успешно обновлен через Google OAuth.")
            except Exception as e:
                self.user_repo.db.rollback()
                logger.error(f"Ошибка при обновлении пользователя '{user.id}' через Google OAuth: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при обновлении пользователя"
                )
        else:
            user_data = {
                'username': google_data.username,
                'email': google_data.email,
                'is_email_verified': google_data.is_email_verified,
                'google_id': google_data.google_id,
                'google_image_url': google_data.google_image_url,
                'google_access_token': google_data.google_access_token,
                'google_refresh_token': google_data.google_refresh_token,
                'google_token_expires_at': google_data.google_token_expires_at,
            }
            try:
                user = self.user_repo.create_user( user_data)
                logger.info(f"Новый пользователь '{user.id}' зарегистрирован через Google OAuth.")
                subject = "Добро пожаловать в TuneWave!"
                body = f"""
                Привет, {google_data.username}!

                Спасибо за регистрацию в TuneWave. Мы рады видеть тебя в нашем музыкальном сообществе.
                Начни создавать комнаты и делиться музыкой с друзьями!

                С уважением,
                Команда TuneWave
                """
                send_email_task.delay(google_data.email, subject, body)
            except Exception as e:
                self.user_repo.db.rollback()
                logger.error(f"Ошибка при создании пользователя через Google OAuth '{google_data.email}': {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при создании пользователя"
                )
            
        from datetime import timedelta
        from app.utils.jwt import create_access_token

        access_token = create_access_token(
            payload={'sub': str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return UserService._map_user_to_response(user), Token(access_token=access_token)
    

    
    async def authenticate_user_with_spotify(
        self,
        spotify_data: SpotifyOAuthData
    ) -> tuple[UserResponse,Token]:
        """
        Аутентифицирует пользователя через Spotify OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """
        user = self.user_repo.get_user_by_email(spotify_data.email)
        if not user:
            logger.warning(f'Пользователь не найден {spotify_data.email}')
            user = self.user_repo.get_user_by_spotify_id(spotify_data.spotify_id)

        

        if user:
            global_ban = BanRepository.is_user_banned_global(user.id)
            if global_ban:
                logger.warning(f"Попытка входа забаненного пользователя Spotify: ID '{user.id}'.")
                raise HTTPException(
                    status_code=403,
                    detail="Ваш аккаунт заблокирован. Свяжитесь с поддержкой для получения дополнительной информации."
                )
            update_data = {}
            if not user.spotify_id:
                update_data['spotify_id'] = spotify_data.spotify_id
                update_data['spotify_image_url'] = spotify_data.spotify_image_url
                update_data['spotify_profile_url'] = spotify_data.spotify_profile_url

            # Всегда обновляем токены Spotify и время их истечения, так как они имеют срок годности
            update_data['spotify_access_token'] = spotify_data.spotify_access_token
            update_data['spotify_refresh_token'] = spotify_data.spotify_refresh_token
            update_data['spotify_token_expires_at'] = spotify_data.spotify_token_expires_at
            update_data['spotify_scope'] = spotify_data.spotify_scope

            try:
                if update_data:
                    user = self.user_repo.update_user(user,update_data)
                    logger.info(f"Пользователь '{user.id}' успешно обновлен через Spotify OAuth.")
            except Exception as e:
                self.user_repo.db.rollback()
                logger.error(f"Ошибка при обновлении пользователя '{user.id}' через Spotify OAuth: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при создании пользователя"
                )

        else:
            user_data = {
                'username': spotify_data.username,
                'email': spotify_data.email,
                'is_email_verified': False,
                'spotify_id': spotify_data.spotify_id,
                'spotify_profile_url': spotify_data.spotify_profile_url,
                'spotify_image_url': spotify_data.spotify_image_url,
                'spotify_access_token': spotify_data.spotify_access_token,
                'spotify_refresh_token': spotify_data.spotify_refresh_token,
                'spotify_token_expires_at': spotify_data.spotify_token_expires_at,
                'spotify_scope': spotify_data.spotify_scope
            }

            try:
                user = self.user_repo.create_user(user_data)
                logger.info(f"Новый пользователь '{user.id}' зарегистрирован через Spotify OAuth.")
                subject = "Добро пожаловать в TuneWave!"
                body = f"""
                Привет, {spotify_data.username}!

                Спасибо за регистрацию в TuneWave. Мы рады видеть тебя в нашем музыкальном сообществе.
                Начни создавать комнаты и делиться музыкой с друзьями!

                С уважением,
                Команда TuneWave
                """
                send_email_task.delay(spotify_data.email, subject, body)
            except Exception as e:
                self.user_repo.db.rollback()
                logger.error(f"Ошибка при создании пользователя через Spotify OAuth '{spotify_data.email}': {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при создании пользователя"
                )
        
        from datetime import timedelta
        from app.utils.jwt import create_access_token

        access_token = create_access_token(
            payload={'sub': str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return UserService._map_user_to_response(user), Token(access_token=access_token)
    

    
    def get_user_by_token(self,token: str) -> User:
        """_summary_

        Args:
            db (Session): _description_
            token (str): _description_

        Returns:
            User: _description_
        """
        try:
            payload = decode_access_token(token)
            user_id = payload.get('sub')
            if not user_id:
                logger.warning("Ошибка декодирования токена: отсутствует 'sub' (ID пользователя).")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Невалидный токен: отсутствует ID пользователя'
                )
            user = UserService.get_user_by_id(user_id)
            return user
        except exceptions.DecodeError:
            logger.warning("Невалидный JWT-токен: ошибка декодирования.")
            raise HTTPException(
                status_code=401,
                detail='Невалидный токен'
            )
        

    
    
    async def load_avatar(self,user: User,avatar_file: UploadFile) -> UserResponse:
        """
        Загружает файл аватарки, сохраняет его и обновляет URL в профиле пользователя.

        Args:
            db (Session): Сессия базы данных.
            user (User): Объект текущего пользователя.
            avatar_file (UploadFile): Загруженный файл изображения.

        Raises:
            HTTPException: Если файл не соответствует требованиям (тип, размер).
            Exception: В случае внутренней ошибки сервера при сохранении/обновлении.

        Returns:
            UserResponse: Обновленный объект пользователя с новым URL аватарки.
        """
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if avatar_file.content_type not in allowed_types:
            logger.warning(f"Загруженный файл аватара имеет недопустимый тип: '{avatar_file.content_type}'.")
            raise HTTPException(
                status_code=400,
                detail='Изображение не соответстует нужному типу'
            )
        
        content = await avatar_file.read()
        if len(content) > settings.MAX_AVATAR_SIZE_BYTES:
            logger.warning(f"Размер загруженного файла аватара ({len(content)} байт) превышает лимит ({settings.MAX_AVATAR_SIZE_BYTES} байт).")
            raise HTTPException(
                status_code=400,
                detail='Ограничения размера файла 5мб'
            )
        file_extension = avatar_file.filename.split('.')[-1] if '.' in avatar_file.filename else 'png'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        file_path = settings.AVATARS_STORAGE_DIR / unique_filename

        try:
            with open(f"{file_path}", 'wb') as f:
                f.write(content)

            new_avatar_url = f"{settings.BASE_URL}/avatars/{unique_filename}"
            
            updated_user = await UserService.update_user_profile(
                 
                user.id, 
                UserUpdate(avatar_url=new_avatar_url)
            )
            logger.info(f"Аватар пользователя '{user.id}' успешно загружен и обновлен. URL: {new_avatar_url}")
            return updated_user
            
        except Exception as e:
            self.user_repo.db.rollback()
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Ошибка сервера при загрузке аватара для пользователя '{user.id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка сервера при загрузке аватара"
            )
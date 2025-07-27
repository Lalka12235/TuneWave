from fastapi import HTTPException,status
from app.repositories.user_repo import UserRepository
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schemas import UserResponse, UserCreate, UserUpdate,Token,GoogleOAuthData, SpotifyOAuthData
import uuid
from typing import Any
from app.config.settings import settings



class UserService:


    @staticmethod
    def _check_for_existing_user_and_raise_if_found(
        db: Session,
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
            user = UserRepository.get_user_by_email(db, email)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Пользователь с email '{email}' уже существует."
                )
        
        if google_id:
            user = UserRepository.get_user_by_google_id(db, google_id)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Пользователь с Google ID '{google_id}' уже существует."
                )
        
        if spotify_id:
            user = UserRepository.get_user_by_spotify_id(db, spotify_id)
            if user and (exclude_user_id is None or user.id != exclude_user_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Пользователь с Spotify ID '{spotify_id}' уже существует."
                )


    @staticmethod
    def _map_user_to_response(user: User) -> UserResponse:
        """
        Вспомогательный метод для преобразования объекта User SQLAlchemy в Pydantic UserResponse.
        Это централизованное место для форматирования данных, возвращаемых клиенту.
        """
        # Pydantic's model_validate() автоматически преобразует SQLAlchemy ORM-объект
        # в Pydantic-модель, благодаря Config.from_attributes = True в UserResponse.
        return UserResponse.model_validate(user)


    @staticmethod
    def get_user_by_id(db: Session,user_id: uuid.UUID) -> dict[str,Any]:
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
        user = UserRepository.get_user_by_id(db,user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    
    @staticmethod
    def get_user_by_email(db: Session,email: str) -> UserResponse:
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
        user = UserRepository.get_user_by_email(db,email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    

    @staticmethod
    def get_user_by_spotify_id(db: Session, spotify_id: str) -> UserResponse:
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
        user = UserRepository.get_user_by_spotify_id(db,spotify_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    
    
    @staticmethod
    def get_user_by_google_id(db: Session,google_id: str) -> UserResponse:
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
        user = UserRepository.get_user_by_google_id(db,google_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        return UserService._map_user_to_response(user)
    


    @staticmethod
    def create_user(db: Session,user_data: UserCreate) -> UserResponse:
        """Создание пользователя

        Args:
            db (Session): Сессия базы данных.
            user_data (UserCreate): Данные для создания пользоателя

        Returns:
            UserResponse: Информация о создании
        """
        user = UserService._check_for_existing_user_and_raise_if_found(
            db,
            user_data.email,
            user_data.google_id,
            user_data.spotify_id
        )

        new_user = UserRepository.create_user(db,user_data.model_dump())

        return UserService._map_user_to_response(new_user)
    
    @staticmethod
    async def update_user_profile(db: Session, user_id: uuid.UUID, update_data: UserUpdate) -> UserResponse:
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
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден."
            )
        
        data_to_update = update_data.model_dump(exclude_unset=True) 

        updated_user = UserRepository.update_user(db, user, data_to_update)

        return UserService._map_user_to_response(updated_user)
    

    @staticmethod
    def hard_delete_user(db: Session,user_id: uuid.UUID) -> dict[str,Any]:
        """_summary_

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя для физического удаления.

        Raises:
            HTTPException: Пользователь не найден(404)

        Returns:
            dict[str,Any]: Информация об удалении
        """
        user = UserRepository.get_user_by_id(db,user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        
        del_user = UserRepository.hard_delete_user(db,user_id)

        return {
            'detail': 'delete user',
            'status': 'success',
            'id': user_id,
        }
    

    @staticmethod
    def authenticate_user_with_google(db: Session, google_data: GoogleOAuthData) -> tuple[UserResponse, Token]:
        """
        Аутентифицирует пользователя через Google OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """
        user = UserRepository.get_user_by_email(db,google_data.email)
        if not user:
            user = UserRepository.get_user_by_google_id(db,google_data.google_id)

        
        if user:
            update_data = {}
            if not user.google_id:
                update_data['google_id'] = google_data.google_id
                update_data['google_image_url'] = google_data.google_image_url
            if google_data.is_email_verified and not user.is_email_verified:
                update_data['is_email_verified'] = True
            
            if update_data:
                user = UserRepository.update_user(db,user,update_data)

        else:
            user_data = {
                'username': google_data.username,
                'email': google_data.email,
                'is_email_verified': google_data.is_email_verified,
                'google_id': google_data.google_id,
                'google_image_url': google_data.google_image_url,
            }

            user = UserRepository.create_user(db,user_data)

        
        from datetime import timedelta
        from app.utils.jwt import create_access_token

        access_token = create_access_token(
            payload={'sub': str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )


        return UserService._map_user_to_response(user), Token(access_token=access_token)
    

    @staticmethod
    def authenticate_user_with_spotify(
        db: Session,
        spotify_data: SpotifyOAuthData
    ) -> tuple[UserResponse,Token]:
        """
        Аутентифицирует пользователя через Spotify OAuth.
        Создает или обновляет пользователя в БД и возвращает JWT-токен вашего приложения.
        """
        user = UserRepository.get_user_by_email(db,spotify_data.email)
        if not user:
            user = UserRepository.get_user_by_spotify_id(db,spotify_data.spotify_id)

        if user:
            update_data = {}
            if not user.spotify_id:
                update_data['spotify_id'] = spotify_data.spotify_id
                update_data['spotify_image_url'] = spotify_data.spotify_image_url
                update_data['spotify_profile_url'] = spotify_data.spotify_profile_url

            # Всегда обновляем токены Spotify и время их истечения, так как они имеют срок годности
            update_data['spotify_access_token'] = spotify_data.spotify_access_token
            update_data['spotify_refresh_token'] = spotify_data.spotify_refresh_token
            update_data['spotify_token_expires_at'] = spotify_data.spotify_token_expires_at


            if update_data:
                user = UserRepository.update_user(db,user,update_data)

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
                'spotify_token_expires_at': spotify_data.spotify_token_expires_at
            }

            user = UserRepository.create_user(db,user_data)
        
        from datetime import timedelta
        from app.utils.jwt import create_access_token

        access_token = create_access_token(
            payload={'sub': str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return UserService._map_user_to_response(user), Token(access_token=access_token)
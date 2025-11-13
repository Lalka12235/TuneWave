from sqlalchemy import select,delete
from app.infrastructure.db.models import User
from sqlalchemy.orm import Session
import uuid
from app.domain.interfaces.user_repo import UserRepository
from app.domain.entity import UserEntity


class SQLalchemyUserRepository(UserRepository):
    """
    Реализация User Репозитория 
    """

    def __init__(self,db : Session):
        self._db = db
    
    def from_model_to_entity(self,model: User) -> UserEntity | None:
        return UserEntity(
            id=model.id,
            username=model.username,
            email=model.email,
            is_email_verified=model.is_email_verified,
            avatar_url=model.avatar_url,
            bio=model.bio,
            google_id=model.google_id,
            google_image_url=model.google_image_url,
            spotify_id=model.spotify_id,
            spotify_profile_url=model.spotify_profile_url,
            spotify_image_url=model.spotify_image_url,
        )

    
    def get_user_by_id(self, user_id: uuid.UUID) -> UserEntity | None:
        """
        Получает пользователя по его уникальному ID.
        
        Args:
            user_id (uuid.UUID): Уникальный идентификатор пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(
            User.id == user_id
        )
        result = self._db.execute(stmt)
        result = result.scalar_one_or_none()
        return self.from_model_to_entity(result)

    
    def get_user_by_email(self, email: str) -> UserEntity | None:
        """
        Получает пользователя по его email.
        
        Args:
            email (str): Email пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(User.email == email)
        result = self._db.execute(stmt)
        result =  result.scalar_one_or_none()
        return self.from_model_to_entity(result)

    
    def get_user_by_google_id(self, google_id: str) -> UserEntity | None:
        """
        Получает пользователя по его Google ID.
        
        Args:
            google_id (str): Google ID пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(User.google_id == google_id)
        result = self._db.execute(stmt)
        result =  result.scalar_one_or_none()
        return self.from_model_to_entity(result)

    
    def get_user_by_spotify_id(self, spotify_id: str) -> UserEntity | None:
        """
        Получает пользователя по его Spotify ID.
        
        Args:
            spotify_id (str): Spotify ID пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(User.spotify_id == spotify_id)
        result = self._db.execute(stmt)
        result =  result.scalar_one_or_none()
        return self.from_model_to_entity(result)
    
    def create_user(self, user_data: dict[str, str]) -> UserEntity:
        """
        Создает нового пользователя в базе данных.
        
        Args:
            user_data (dict): Словарь с данными пользователя (например, email, username, google_id, spotify_id).
                              Должен содержать как минимум 'email' и 'username'.
            
        Returns:
            User: Созданный объект User.
            
        """
        new_user = User(
            username=user_data['username'],
            email=user_data['email'],
            is_email_verified=user_data.get('is_email_verified', False),
            google_id=user_data.get('google_id'),
            google_image_url=user_data.get('google_image_url'),
            spotify_id=user_data.get('spotify_id'),
            spotify_profile_url=user_data.get('spotify_profile_url'),
            spotify_image_url=user_data.get('spotify_image_url'),
        )

        self._db.add(new_user)
        self._db.flush()
        self._db.refresh(new_user)
        return self.from_model_to_entity(new_user)
    
    
    def update_user(self, user_entity: UserEntity, update_data: dict[str, str]) -> UserEntity:
        """
        Обновляет существующего пользователя в базе данных.
        
        Args:
            user_entity (User): Объект пользователя, который нужно обновить.
            update_data (dict): Словарь с данными для обновления. Ключи словаря
                                должны соответствовать именам полей модели User.
            
        Returns:
            User: Обновленный объект User.
        """
        user = self._db.execute(select(User).where(User.id == user_entity.id))
        for key, value in update_data.items():
            setattr(user, key, value)
        
        self._db.add(user)
        self._db.flush()
        self._db.refresh(user)
        return self.from_model_to_entity(user)
    
    def hard_delete_user(self, user_id: uuid.UUID) -> bool:
        """
        Полностью удаляет пользователя из базы данных.
        Использовать с крайней осторожностью, так как данные будут безвозвратно утеряны.
        
        Args:
            user_id (uuid.UUID): ID пользователя для физического удаления.
            
        Returns:
            bool: True, если пользователь был удален, иначе False.
        """
        stmt = delete(User).where(User.id == user_id)
        result = self._db.execute(stmt)
        return result.rowcount > 0 
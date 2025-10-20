from sqlalchemy import select,delete
from app.models.user import User
from sqlalchemy.orm import Session
import uuid

class UserRepository:

    def __init__(self,db : Session):
        self._db = db

    
    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Получает пользователя по его уникальному ID.
        
        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): Уникальный идентификатор пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(
            User.id == user_id
        )
        result = self._db.execute(stmt)
        return result.scalar_one_or_none()

    
    def get_user_by_email(self, email: str) -> User | None:
        """
        Получает пользователя по его email.
        
        Args:
            db (Session): Сессия базы данных.
            email (str): Email пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(User.email == email)
        result = self._db.execute(stmt)
        return result.scalar_one_or_none()

    
    def get_user_by_google_id(self, google_id: str) -> User | None:
        """
        Получает пользователя по его Google ID.
        
        Args:
            db (Session): Сессия базы данных.
            google_id (str): Google ID пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(User.google_id == google_id)
        result = self._db.execute(stmt)
        return result.scalar_one_or_none()

    
    def get_user_by_spotify_id(self, spotify_id: str) -> User | None:
        """
        Получает пользователя по его Spotify ID.
        
        Args:
            db (Session): Сессия базы данных.
            spotify_id (str): Spotify ID пользователя.
            
        Returns:
            User | None: Объект User, если найден, иначе None.
        """
        stmt = select(User).where(User.spotify_id == spotify_id)
        result = self._db.execute(stmt)
        return result.scalar_one_or_none()
    
    
    def create_user(self, user_data: dict) -> User:
        """
        Создает нового пользователя в базе данных.
        
        Args:
            db (Session): Сессия базы данных.
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
            spotify_access_token=user_data.get('spotify_access_token'),
            spotify_refresh_token=user_data.get('spotify_refresh_token'),
            spotify_token_expires_at=user_data.get('spotify_token_expires_at')
        )

        self._db.add(new_user)
        self._db.flush() # Используем flush, чтобы получить ID нового пользователя до коммита
        self._db.refresh(new_user) # Обновляем объект, чтобы убедиться, что все поля (включая ID) актуальны
        return new_user
    
    
    def update_user(self, user: User, update_data: dict) -> User:
        """
        Обновляет существующего пользователя в базе данных.
        
        Args:
            db (Session): Сессия базы данных.
            user (User): Объект пользователя, который нужно обновить.
            update_data (dict): Словарь с данными для обновления. Ключи словаря
                                должны соответствовать именам полей модели User.
            
        Returns:
            User: Обновленный объект User.
        """
        # Итерируемся по данным для обновления и устанавливаем соответствующие атрибуты объекта User.
        for key, value in update_data.items():
            setattr(user, key, value)
        
        self._db.add(user) # Добавляем (или повторно добавляем) объект в сессию для отслеживания изменений.
        self._db.flush() # Выполняем операции в БД, но без коммита.
        self._db.refresh(user) # Обновляем объект, чтобы убедиться, что все поля (включая updated_at) актуальны.
        return user


    #
    #def soft_delete_user(self, user_id: uuid.UUID) -> bool:
    #    """
    #    "Мягко" удаляет пользователя, устанавливая его флаг is_active в False.
    #    Данные пользователя остаются в базе данных.
    #    
    #    Args:
    #        db (Session): Сессия базы данных.
    #        user_id (uuid.UUID): ID пользователя для "мягкого" удаления.
    #        
    #    Returns:
    #        bool: True, если пользователь найден и помечен как неактивный, иначе False.
    #    """
    #    user.is_active = False # Устанавливаем флаг неактивности
    #    db.add(user) # Добавляем объект в сессию для сохранения изменения
    #    db.flush() # Применяем изменения в рамках текущей транзакции
    #    return True

    
    def hard_delete_user(self, user_id: uuid.UUID) -> bool:
        """
        Полностью удаляет пользователя из базы данных.
        Использовать с крайней осторожностью, так как данные будут безвозвратно утеряны.
        
        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя для физического удаления.
            
        Returns:
            bool: True, если пользователь был удален, иначе False.
        """
        stmt = delete(User).where(User.id == user_id)
        result = self._db.execute(stmt)
        return result.rowcount > 0 
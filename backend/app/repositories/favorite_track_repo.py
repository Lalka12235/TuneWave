from sqlalchemy import select,delete
from sqlalchemy.orm import Session,joinedload
from app.models import FavoriteTrack
import uuid
from app.schemas.entity import FavoriteTrackEntity
from app.repositories.abc.favorite_track_repo import FavoriteTrackRepository


class SQLalchemyFavoriteTrackRepository(FavoriteTrackRepository):

    def __init__(self, db: Session):
        self._db = db

    
    def from_model_to_entity(self,model: FavoriteTrack) -> FavoriteTrackEntity:
        return FavoriteTrackEntity(
            user_id=model.user_id,
            track_id=model.track_id,
            added_at=model.added_at
        )

    
    def get_favorite_tracks(self, user_id: uuid.UUID) -> list[FavoriteTrackEntity]:
        """
        Получает все записи любимых треков для указанного пользователя,
        включая связанные объекты треков.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): Уникальный ID пользователя.

        Returns:
            list[FavoriteTrack]: Список объектов FavoriteTrack,
                                 каждый из которых включает связанный объект Track.
                                 Возвращает пустой список, если любимых треков нет.
        """
        stmt = select(FavoriteTrack).where(
            FavoriteTrack.user_id == user_id,
        ).options(
            joinedload(FavoriteTrack.track)
        )
        result = self._db.execute(stmt).scalars().all()
        return self.from_model_to_entity(result)
    

    
    def add_favorite_track(self,user_id: uuid.UUID,track_id: uuid.UUID) -> FavoriteTrackEntity:
        """
        Добавляет трек в список избранных треков пользователя.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, который добавляет трек.
            track_id (uuid.UUID): ID трека, который нужно добавить в избранное.

        Returns:
            FavoriteTrack | None: Созданный объект FavoriteTrack при успехе, иначе None.
                                  (Примечание: commit/rollback выполняются в сервисном слое)
        """
        new_favorite_track = FavoriteTrack(
            user_id=user_id,
            track_id=track_id
        )
        self._db.add(new_favorite_track)
        self._db.flush()
        self._db.refresh(new_favorite_track)
        return self.from_model_to_entity(new_favorite_track)
    

    
    def remove_favorite_track(self,user_id: uuid.UUID,track_id: uuid.UUID) -> bool:
        """
        Удаляет трек из списка избранных треков пользователя.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, который удаляет трек.
            track_id (uuid.UUID): ID трека, который нужно удалить из избранного.

        Returns:
            bool: True, если трек был успешно удален, False, если трек не был найден.
                  (Примечание: commit/rollback выполняются в сервисном слое)
        """
        stmt = delete(FavoriteTrack).where(
            FavoriteTrack.user_id == user_id,
            FavoriteTrack.track_id == track_id,
        )
        result = self._db.execute(stmt)
        return result.rowcount > 0
    

    
    def is_favorite_track(self,user_id: uuid.UUID,track_id: uuid.UUID) -> bool:
        """
        Проверяет, является ли указанный трек любимым для данного пользователя.

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя.
            track_id (uuid.UUID): ID трека.

        Returns:
            bool: True, если трек является любимым для пользователя, иначе False.
        """
        stmt = select(FavoriteTrack).where(
            FavoriteTrack.user_id == user_id,
            FavoriteTrack.track_id == track_id,
        )
        result = self._db.execute(stmt)
        return bool(result.first())
from sqlalchemy import select,delete
from sqlalchemy.orm import Session,joinedload
from app.models.favorite_track import FavoriteTrack
from app.models.track import Track
import uuid


class FavoriteTrackRepository:

    @staticmethod
    def get_favorite_tracks(db: Session, user_id: uuid.UUID) -> list[FavoriteTrack]:
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
        result = db.execute(stmt)
        return result.scalars().all()
    

    @staticmethod
    def add_favorite_track(db: Session,user_id: uuid.UUID,track_id: uuid.UUID) -> FavoriteTrack | None:
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
        db.add(new_favorite_track)
        db.refresh(new_favorite_track)
        return new_favorite_track
    

    @staticmethod
    def remove_favorite_track(db: Session,user_id: uuid.UUID,track_id: uuid.UUID) -> bool:
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
        result = db.execute(stmt)
        return result.rowcount > 0
    

    @staticmethod
    def is_favorite_track(db: Session,user_id: uuid.UUID,track_id: uuid.UUID) -> bool:
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
        result = db.execute(stmt)
        return bool(result.first())
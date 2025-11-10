from abc import ABC,abstractmethod
import uuid
from app.schemas.entity import FavoriteTrackEntity


class FavoriteTrackRepository(ABC):

    @abstractmethod
    def get_favorite_tracks(self, user_id: uuid.UUID) -> list[FavoriteTrackEntity]:
        """
        Получает все записи любимых треков для указанного пользователя,
        включая связанные объекты треков.
        """
        raise NotImplementedError()

    @abstractmethod
    def add_favorite_track(self,user_id: uuid.UUID,track_id: uuid.UUID) -> FavoriteTrackEntity:
        """
        Добавляет трек в список избранных треков пользователя.
        """
        raise NotImplementedError()

    @abstractmethod
    def remove_favorite_track(self,user_id: uuid.UUID,track_id: uuid.UUID) -> bool:
        """
        Удаляет трек из списка избранных треков пользователя.
        """
        raise NotImplementedError()

    @abstractmethod
    def is_favorite_track(self,user_id: uuid.UUID,track_id: uuid.UUID) -> bool:
        """
        Проверяет, является ли указанный трек любимым для данного пользователя.
        """
        raise NotImplementedError()
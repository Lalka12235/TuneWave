import uuid
from abc import ABC,abstractmethod
from pathlib import Path

from app.domain.entity import UserEntity


class AvatarStorageGateway(ABC):

    @abstractmethod
    def save_avatar(self,content: bytes,filename: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def delete_avatar(self,user_id: uuid.UUID) -> bool:
        raise NotImplementedError
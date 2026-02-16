import uuid
from abc import ABC,abstractmethod



class AvatarStorageGateway(ABC):

    @abstractmethod
    def save_avatar(self,content: bytes,filename: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def delete_avatar(self,user_id: uuid.UUID) -> bool:
        raise NotImplementedError
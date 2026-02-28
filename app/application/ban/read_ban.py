import uuid
from app.domain.interfaces.ban_gateway import BanGateway
from app.domain.entity import UserEntity


class BanService:
    
    def __init__(self,ban_repo: BanGateway):
        self.ban_repo = ban_repo

 
    def get_bans_by_admin(self,user_id: uuid.UUID) -> list[UserEntity]:
        """
        Получает список банов, выданных указанным пользователем (кто забанил).
        """
        bans = self.ban_repo.get_bans_by_admin(user_id)
        if not bans:
            return []
        
        return [ban for ban in bans]

    
    def get_bans_on_user(self,user_id: uuid.UUID) -> list[UserEntity]:
        """
        Получает список банов, полученных указанным пользователем (кого забанили).
        """
        bans = self.ban_repo.get_bans_on_user(user_id)
        if not bans:
            return []
        
        return [ban for ban in bans]
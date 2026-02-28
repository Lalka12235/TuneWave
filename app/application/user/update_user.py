from app.domain.interfaces.user_gateway import UserGateway
import uuid


class DeleteUser:
    
    def __init__(self,user_repo: UserGateway):
        self.user_repo = user_repo
    
    def hard_delete_user(self, user_id: uuid.UUID) -> dict[str, str]:
        """_summary_

        Args:
            user_id (uuid.UUID): ID пользователя для физического удаления.

        Raises:
            HTTPException: Пользователь не найден(404)

        """
        status_deleted = self.user_repo.hard_delete_user(user_id)

        return {
            "detail": "delete user",
            "status": status_deleted,
            "id": str(user_id),
        }
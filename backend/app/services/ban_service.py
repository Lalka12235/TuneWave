import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.logger.log_config import logger
from app.models.ban import Ban
from app.models.user import User
from app.repositories.ban_repo import BanRepository
from app.schemas.ban_schemas import BanCreate, BanRemove, BanResponse


class BanService:

    def __init__(self,db: Session,ban_repo: BanRepository):
        self._db = db
        self.ban_repo = ban_repo

    @staticmethod
    def _map_ban_to_response(ban: Ban) -> BanResponse:
        """
        Вспомогательный метод для маппинга объекта Ban SQLAlchemy в Pydantic BanResponse.
        """
        return BanResponse.model_validate(ban)

    
    def get_bans_by_admin(self,user_id: uuid.UUID) -> list[BanResponse]:
        """
        Получает список банов, выданных указанным пользователем (кто забанил).

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, который выдал бан.

        Returns:
            List[BanResponse]: Список банов, выданных этим пользователем.
        """
        bans = self.ban_repo.get_bans_by_admin(user_id)
        if not bans:
            return []
        
        return [self._map_ban_to_response(ban) for ban in bans]

    
    def get_bans_on_user(self,user_id: uuid.UUID) -> list[BanResponse]:
        """
        Получает список банов, полученных указанным пользователем (кого забанили).

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, который был забанен.

        Returns:
            List[BanResponse]: Список банов, полученных этим пользователем.
        """
        bans = self.ban_repo.get_bans_on_user(user_id)
        if not bans:
            return []
        
        return [self._map_ban_to_response(ban) for ban in bans]
    

    
    def add_ban(self,data_ban: BanCreate,current_user: User) -> BanResponse:
        """
        Добавляет новый бан для пользователя в комнате или глобально.
        Проверяет, не забанен ли пользователь уже.

        Args:
            db (Session): Сессия базы данных.
            data_ban (BanCreate): Pydantic-схема, содержащая данные для бана (ID забаненного, room_id, причина).
            current_user (User): Текущий аутентифицированный пользователь, который выдает бан.

        Returns:
            BanResponse: Объект BanResponse, представляющий созданный бан.

        Raises:
            HTTPException (400 BAD REQUEST): Если пользователь уже забанен.
            HTTPException (404 NOT FOUND): Если комната или забаненный пользователь не найдены (если логика проверки будет добавлена).
            HTTPException (403 FORBIDDEN): Если у текущего пользователя нет прав (если логика проверки прав будет добавлена).
            HTTPException (500 INTERNAL SERVER ERROR): При внутренних ошибках сервера.
        """
        if data_ban.room_id:
                existing_local_ban = self.ban_repo.is_user_banned_local( data_ban.ban_user_id, data_ban.room_id)
                if existing_local_ban:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Пользователь уже забанен в этой комнате."
                    )
            

        existing_global_ban = self.ban_repo.is_user_banned_global( data_ban.ban_user_id)
        if existing_global_ban:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже забанен глобально."
            )

        try:
            new_ban_entry = self.ban_repo.add_ban(
                ban_user_id=data_ban.ban_user_id,
                room_id=data_ban.room_id,
                reason=data_ban.reason,
                by_ban_user_id=current_user.id
            )
            
            self._db.commit()
            self._db.refresh(new_ban_entry)

            return self._map_ban_to_response(new_ban_entry)
        
        except HTTPException as e:
            self._db.rollback()
            raise e
        except Exception:
            self._db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось добавить бан из-за внутренней ошибки сервера."
            )
        
    
    def remove_ban(self, data_ban: BanRemove) -> dict[str, Any]:
        """
        Удаляет запись о бане пользователя.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            data_ban (BanRemove): Pydantic-схема, содержащая ID забаненного пользователя и room_id (опционально).

        Returns:
            dict[str, Any]: Словарь с сообщением об успешном снятии бана.

        Raises:
            HTTPException (404 NOT FOUND): Если бан не найден.
            HTTPException (500 INTERNAL SERVER ERROR): При внутренних ошибках сервера.
        """
        existing_ban_to_remove = None
        if data_ban.room_id:
            existing_ban_to_remove_local = self.ban_repo.is_user_banned_local( data_ban.ban_user_id, data_ban.room_id)
        else:
            self.ban_repo.is_user_banned_global( data_ban.ban_user_id)
        
        if not existing_ban_to_remove:
                logger.warning(f"BanService: Попытка снять несуществующий бан для user_id={data_ban.ban_user_id}, room_id={data_ban.room_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Бан не найден или уже был снят."
                )
        try:
            if existing_ban_to_remove_local:
                self.ban_repo.remove_ban_local(data_ban.room_id,data_ban.ban_user_id)
            else:
                self.ban_repo.remove_ban_global(data_ban.ban_user_id)
            self._db.commit()
            logger.info(f"BanService: Бан успешно снят для user_id={data_ban.ban_user_id}, room_id={data_ban.room_id}")
            
            return {
                "status": "success",
                "detail": "Бан успешно снят."
            }

        except HTTPException as e:
            self._db.rollback()
            logger.warning(
                f"HTTPException при снятии бана. user_id: {data_ban.ban_user_id}, "
                f"room_id: {data_ban.room_id if data_ban.room_id else 'глобальный'}. Ошибка: {e.detail}",
                exc_info=True
            )
            raise e
        except Exception as e:
            self._db.rollback()
            logger.error(
                f"Внутренняя ошибка сервера при снятии бана. user_id: {data_ban.ban_user_id}, "
                f"room_id: {data_ban.room_id if data_ban.room_id else 'глобальный'}. Ошибка: {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось снять бан из-за внутренней ошибки сервера: {e}" 
            )


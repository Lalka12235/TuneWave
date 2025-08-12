from fastapi import HTTPException,status
from app.repositories.ban_repo import BanRepository
import uuid
from sqlalchemy.orm import Session
from app.schemas.ban_schemas import BanResponse,BanCreate,BanRemove
from app.models.ban import Ban
from app.models.user import User
from typing import Any


class BanService:

    def _map_ban_to_response(ban: Ban) -> BanResponse:
        """
        Вспомогательный метод для маппинга объекта Ban SQLAlchemy в Pydantic BanResponse.
        """
        return BanResponse.model_validate(ban)

    @staticmethod
    def get_bans_by_admin(db: Session,user_id: uuid.UUID) -> list[BanResponse]:
        """
        Получает список банов, выданных указанным пользователем (кто забанил).

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, который выдал бан.

        Returns:
            List[BanResponse]: Список банов, выданных этим пользователем.
        """
        bans = BanRepository.get_bans_by_admin(db,user_id)
        if not bans:
            return []
        
        return [BanService._map_ban_to_response(ban) for ban in bans]

    @staticmethod
    def get_bans_on_user(db: Session,user_id: uuid.UUID) -> list[BanResponse]:
        """
        Получает список банов, полученных указанным пользователем (кого забанили).

        Args:
            db (Session): Сессия базы данных.
            user_id (uuid.UUID): ID пользователя, который был забанен.

        Returns:
            List[BanResponse]: Список банов, полученных этим пользователем.
        """
        bans = BanRepository.get_bans_on_user(db,user_id)
        if not bans:
            return []
        
        return [BanService._map_ban_to_response(ban) for ban in bans]
    

    @staticmethod
    def add_ban(db: Session,data_ban: BanCreate,current_user: User) -> BanResponse:
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
                existing_local_ban = BanRepository.is_user_banned_local(db, data_ban.ban_user_id, data_ban.room_id)
                if existing_local_ban:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Пользователь уже забанен в этой комнате."
                    )
            

        existing_global_ban = BanRepository.is_user_banned_global(db, data_ban.ban_user_id)
        if existing_global_ban:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже забанен глобально."
            )

        try:
            new_ban_entry = BanRepository.add_ban(
                db,
                ban_user_id=data_ban.ban_user_id,
                room_id=data_ban.room_id,
                reason=data_ban.reason,
                by_ban_user_id=current_user.id
            )
            
            db.commit()
            db.refresh(new_ban_entry)

            return BanService._map_ban_to_response(new_ban_entry)
        
        except HTTPException as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось добавить бан из-за внутренней ошибки сервера."
            )
        
    @staticmethod
    def remove_ban(db: Session, data_ban: BanRemove) -> dict[str, Any]:
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
            existing_ban_to_remove = BanRepository.is_user_banned_local(db, data_ban.ban_user_id, data_ban.room_id)
        else:
            existing_ban_to_remove = BanRepository.is_user_banned_global(db, data_ban.ban_user_id)
        
        if not existing_ban_to_remove:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Бан не найден или уже был снят."
                )
        try:
            removed_successfully = False
            if data_ban.room_id:
                removed_successfully = BanRepository.remove_ban_local(db, data_ban.ban_user_id, data_ban.room_id) # <-- ИСПРАВЛЕН ПОРЯДОК АРГУМЕНТОВ
            else:
                removed_successfully = BanRepository.remove_ban_global(db, data_ban.ban_user_id)
            
            if not removed_successfully:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Не удалось снять бан из-за внутренней ошибки сервера."
                )
            
            db.commit()

            return {
                "status": "success",
                "detail": "Бан успешно снят."
            }

        except HTTPException as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось снять бан из-за внутренней ошибки сервера."
            )


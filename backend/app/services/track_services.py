from app.repositories.track_repo import TrackRepository
from app.schemas.track_schema import (
    TrackSchema,
    GetTrackSchema,
    UpdateTrackSchema, 
    DeleteTrackSchema
)
from fastapi import HTTPException, status
from app.services.user_services import UserServices

import logging

logger = logging.getLogger(__name__)


class TrackServices:

    @staticmethod
    def get_track(track: GetTrackSchema):
        tracks = TrackRepository.get_track(track)
        logger.debug(f'Попытка получить трек: {track.title}')
        
        if tracks is None:
            logger.error(f'Трек не найден: {track.title}')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        logger.info(f'Трек найден: {track.title}')
        return {'message': 'get track','detail': tracks}
    
    
    @staticmethod
    def create_track(username: str,track: TrackSchema):
        logger.debug(f'Попытка создания трека')
        tracks = TrackRepository.get_track(track)
        user = UserServices.get_user(username)
        
        if tracks:
            logger.error(f'Ошибка в создание трека')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Track is exist'
            )
        logger.info(f'Трек успешно создан')
        result = TrackRepository.create_track(track,user.id)


        return {'message': 'create track','detail': result}
    

    @staticmethod
    def update_track(upd_track: UpdateTrackSchema):
        logger.debug(f'Попытка обновления трека')
        tracks = TrackRepository.get_track(upd_track)
        
        if tracks is None:
            logger.error(f'Трек не найден: {upd_track.title}')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        logger.info(f'Трек обновлен')
        result = TrackRepository.update_track(upd_track)

        return {'message': 'update track','detail': result}
    

    @staticmethod
    def delete_track(username: str,del_track: DeleteTrackSchema):
        logger.debug(f'Попытка удаления трека')
        tracks = TrackRepository.get_track(del_track)
        user = UserServices.get_user(username)
        
        if tracks is None:
            logger.error(f'Ошибка в удаление трека')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        result = TrackRepository.delete_track(del_track,user.id)
        logger.info(f'Трек успешно удален')
        return {'message': 'delete track','detail': result}
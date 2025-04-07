from app.repositories.track_repo import TrackRepository
from backend.app.schemas.track_schema import (
    TrackSchema,
    GetTrackSchema,
    UpdateTrackSchema, 
    DeleteTrackSchema
)
from fastapi import HTTPException, status
from app.services.user_services import UserServices


class TrackServices:

    @staticmethod
    async def get_track(track: GetTrackSchema):
        tracks =await TrackRepository.get_track(track)
        
        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        return {'message': 'get track','detail': tracks}
    
    
    @staticmethod
    async def create_track(username: str,track: TrackSchema):
        tracks =await TrackRepository.get_track(track)
        user =await UserServices.get_user(username)
        
        if tracks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Track is exist'
            )
        
        result =await TrackRepository.create_track(track,user.id)


        return {'message': 'create track','detail': result}
    

    @staticmethod
    async def update_track(upd_track: UpdateTrackSchema):
        tracks =await TrackRepository.get_track(upd_track)
        
        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        result =await TrackRepository.update_track(upd_track)

        return {'message': 'update track','detail': result}
    

    @staticmethod
    async def delete_track(username: str,del_track: DeleteTrackSchema):
        tracks =await TrackRepository.get_track(del_track)
        user =await UserServices.get_user(username)
        
        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        result =await TrackRepository.delete_track(del_track,user.id)

        return {'message': 'delete track','detail': result}
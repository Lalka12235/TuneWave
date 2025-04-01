from app.repositories.track_repo import TrackRepository
from backend.app.schemas.track_schema import (
    TrackSchema,
    GetTrackSchema,
    UpdateTrackSchema, 
    DeleteTrackSchema
)
from fastapi import HTTPException, status


class TrackServices:

    @staticmethod
    def get_track(track: GetTrackSchema):
        tracks = TrackRepository.get_track(track)
        
        if not tracks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        return {'message': 'get track','detail': tracks}
    
    
    @staticmethod
    def create_track(track: TrackSchema):
        tracks = TrackRepository.get_track(track)
        
        if tracks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Track is exist'
            )
        
        result = TrackRepository.create_track(track)
        
        return {'message': 'create track','detail': result}
    

    @staticmethod
    def update_track(upd_track: UpdateTrackSchema):
        tracks = TrackRepository.get_track(upd_track)
        
        if not tracks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        result = TrackRepository.update_track(upd_track)

        return {'message': 'update track','detail': result}
    

    @staticmethod
    def delete_track(del_track: DeleteTrackSchema):
        tracks = TrackRepository.get_track(del_track)
        
        if not tracks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        result = TrackRepository.delete_track(del_track)

        return {'message': 'delete track','detail': result}
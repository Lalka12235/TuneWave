from fastapi import HTTPException, status, Depends
from app.repositories.room_repo import RoomRepository

from app.auth.auth import get_current_user,check_authorization

class PlayerService:

    @staticmethod
    def start_track(room_name: str, current_user: str = Depends(get_current_user), _ = Depends(check_authorization)):
        room = RoomRepository.get_room_on_name(room_name)
        
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        queue = RoomRepository.get_track_queue(room.id)
        if not queue:
            raise HTTPException(status_code=400, detail="Queue is empty")

        first_track = queue[0]
        RoomRepository.set_current_track(room.id, first_track.track_id)
        RoomRepository.change_state_player(room.id, "playing")

        return {"message": "Track started", "track_id": first_track.track_id}
    

    @staticmethod
    def pause_track(room_name: str,current_user: str = Depends(get_current_user), _ = Depends(check_authorization)):
        room = RoomRepository.get_room_on_name(room_name)
        
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        if room.current_track_id is None:
            raise HTTPException(status_code=400, detail="No track is currently playing")

        RoomRepository.change_state_player(room.id, "paused")

        return {"message": "Playback paused"}
    

    @staticmethod
    def skip_track(room_name: str,current_user: str = Depends(get_current_user), _ = Depends(check_authorization)):
        room = RoomRepository.get_room_on_name(room_name)
        
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        queue = RoomRepository.get_track_queue(room.id)
        if not queue:
            raise HTTPException(status_code=400, detail="Queue is empty")
        
        current = queue[0]
        RoomRepository.del_track_from_queue(room.id,current.track_id)


        if len(queue) > 1:
            next_track = queue[1]
            RoomRepository.set_current_track(room.id,next_track.track_id)
            RoomRepository.change_state_player(room.id,'playing')
            return {'message': 'Skipped to next track', 'track_id': next_track.track_id}
        else:
            RoomRepository.set_current_track(room.id,None)
            RoomRepository.change_state_player(room.id,'paused')
            return {'message': 'Queue is empty'}
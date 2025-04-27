from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.repositories.track_repo import TrackRepository

from app.schemas.track_schema import GetTrackSchema
from app.schemas.room_schema import RoomSchema, UpdRoomSchema

from fastapi import HTTPException,status

from app.utils.hash import make_hash_pass,verify_pass

from datetime import datetime

import logging

logger = logging.getLogger(__name__)

class RoomServices:

    @staticmethod
    def get_room_or_404(room_name):
        room =  RoomRepository.get_room_on_name(room_name)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return room
    

    @staticmethod
    def get_user_or_404(username):
        user =  UserRepository.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


    @staticmethod
    def get_room_on_name(name: str):

        room =  RoomServices.get_room_or_404(name)
        
        return {'message': 'get room on name','detail': room}
    
    
    @staticmethod
    def get_all_room():
        rooms = RoomRepository.get_all_room()

        if rooms is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='No one Rooms'
            )
        
        return {'message': 'get all rooms','detail': rooms}
    

    @staticmethod
    def get_members_from_room(room_name: str):
        room =  RoomServices.get_room_or_404(room_name)
        
        members = RoomRepository.get_members_from_room(room_name)

        return {'message': 'all members','detail': members}


    @staticmethod
    def create_room(username: str,room_setting: RoomSchema):
        user =  RoomServices.get_user_or_404(username)
        
        hash_pass = make_hash_pass(room_setting.password) if room_setting.private and room_setting.password else None
        
        room = RoomRepository.create_room(user.id,room_setting.name,room_setting.max_member,room_setting.private,hash_pass)

        return {'message': 'create room','detail': room}
    

    @staticmethod
    def update_room(username: str , upd_room: UpdRoomSchema):
        user =  RoomServices.get_user_or_404(username)
        
        RoomRepository.update_room(user.id,upd_room.name,upd_room.new_name,upd_room.max_member,upd_room.private)

        return {'message': 'update room','detail': ''}
    

    @staticmethod
    def delete_room(username: str):
        user =  RoomServices.get_user_or_404(username)
        
        RoomRepository.delete_room(user.id)

        return {'message': 'delete room','detail': ''}
    

    @staticmethod
    def set_current_track(room_name: str, track: GetTrackSchema):
        tracks = TrackRepository.get_track(track)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        room =  RoomServices.get_room_or_404(room_name)

        RoomRepository.set_current_track(room.id,tracks.id)

        return {'message': 'set current track', 'detail': ''}


    @staticmethod
    def get_current_track(room_name: str):
        room =  RoomServices.get_room_or_404(room_name)
        
        RoomRepository.get_current_track(room.id)

        return {'message': 'get current track', 'detail': ''}
    


    @staticmethod
    def get_track_queue(room_name: str):
        room =  RoomServices.get_room_or_404(room_name)

        queue = RoomRepository.get_track_queue(room.id)

        return {'message': 'track queue', 'detail': queue}

    

    @staticmethod
    def add_track_to_queue(username: str, room_name: str,track: GetTrackSchema):
        user =  RoomServices.get_user_or_404(username)
        

        tracks = TrackRepository.get_track(track)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        room =  RoomServices.get_room_or_404(room_name)
        
        if user.id == room.owner_id:
            RoomRepository.add_track_to_queue(user.id, track)
            return {'message': 'add track to room','detail': ''}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='None'
            )
    

    @staticmethod
    def del_track_from_queue(username: str,room_name: str ,track: GetTrackSchema):
        user =  RoomServices.get_user_or_404(username)
        
        
        room =  RoomServices.get_room_or_404(room_name)
        
        tracks = RoomRepository.get_track_queue(room.id)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found',
            )
        
        if user.id == room.owner_id:
            RoomRepository.del_track_from_queue(room.id,track)
            return {'message': 'del track from room', 'detail': ''}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='None'
            )


    @staticmethod
    def skip_track_queue(room_name: str):
        room =  RoomServices.get_room_or_404(room_name)
        
        RoomRepository.skip_track_queue(room.id)

        return {'message': 'skip track','detail': ''}



    @staticmethod
    def join_room(username: str, room_name: str, password: str | None = None):
        user =  RoomServices.get_user_or_404(username)

        room =  RoomServices.get_room_or_404(room_name)

        if room.is_private:
            if not password:
                raise HTTPException(status_code=403, detail="Password required for this room")
            if not verify_pass(password, room.password_hash):
                raise HTTPException(status_code=403, detail="Invalid password")
            
        members = [member['username'] for member in  RoomRepository.get_members_from_room(room_name)]

        if len(members) >= room.max_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Room is full'
            )

        RoomRepository.add_user_to_room(user.id, room.id)

        return {"message": "Joined room", "detail": room_name}
    

    @staticmethod
    def leave_room(username: str, room_name: str,):
        user =  RoomServices.get_user_or_404(username)

        room =  RoomServices.get_room_or_404(room_name)
        
        
        RoomRepository.del_user_from_room(user.id,room.id)
        return {'message': 'leave room', 'detail': room_name}
    

    @staticmethod
    def kick_member(owner_name: str,username: str, room_name: str):
        user =  RoomServices.get_user_or_404(username)
        
        owner = UserRepository.get_user(owner_name)
        

        room =  RoomServices.get_room_or_404(room_name)
        
        
        if owner.id == room.owner_id:
            RoomRepository.del_user_from_room(user.id,room.id)
            return {'message': 'leave room', 'detail': room_name}
        
    
    @staticmethod
    def ban_user_in_room(owner_name: str,username: str, room_name: str,ban_expired: datetime):
        user =  RoomServices.get_user_or_404(username)
        
        owner = UserRepository.get_user(owner_name)
        
        room =  RoomServices.get_room_or_404(room_name)
        
        existing_ban =  RoomRepository.get_ban_for_user(user.id, room.id)
        if existing_ban:
            raise HTTPException(status_code=400, detail="User is already banned.")
        
        if owner.id == room.owner_id:
            RoomRepository.ban_user_in_room(user.id,room.id,ban_expired)
            return {'message': 'leave room', 'detail': room_name}
        
    
    @staticmethod
    def unban_user_in_room(owner_name: str,username: str, room_name: str):
        user =  RoomServices.get_user_or_404(username)
        
        owner = UserRepository.get_user(owner_name)
        

        room =  RoomServices.get_room_or_404(room_name)
        
        
        if owner.id == room.owner_id:
            RoomRepository.unban_user_in_room(user.id,room.id)
            return {'message': 'leave room', 'detail': room_name} 
        
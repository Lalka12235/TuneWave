from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.repositories.track_repo import TrackRepository

from app.schemas.track_schema import GetTrackSchema

from fastapi import HTTPException,status

from app.utils.hash import make_hash_pass,verify_pass

from datetime import datetime

class RoomServices:

    @staticmethod
    def get_room_on_name(name: str):
        room = RoomRepository.get_room_on_name(name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
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
        room = RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        members = RoomRepository.get_members_from_room(room_name)

        return {'message': 'all members','detail': members}


    @staticmethod
    def create_room(username: str,name: str, max_member: int, private: bool, password: str | None = None):
        user =  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        hash_pass = make_hash_pass(password) if private and password else None
        
        room = RoomRepository.create_room(user.id,name,max_member,private,hash_pass)

        return {'message': 'create room','detail': room}
    

    @staticmethod
    def update_room(username: str , name: str,new_name: str, max_member: int, private: bool):
        user =  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        upd_room = RoomRepository.update_room(user.id,name,new_name,max_member,private)

        return {'message': 'update room','detail': ''}
    

    @staticmethod
    def delete_room(username: str):
        user =  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        deL_room = RoomRepository.delete_room(user.id)

        return {'message': 'delete room','detail': ''}
    

    @staticmethod
    def add_track_to_room(owner_name: str,username: str, room_name: str,track: GetTrackSchema):
        user =  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        owner = UserRepository.get_user(owner_name)

        tracks = TrackRepository.get_track(track)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        room = RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        if owner.id == room.id:
            RoomRepository.add_track_to_room(user.id, track)
            return {'message': 'add track to room','detail': ''}
    

    @staticmethod
    def del_track_from_room(owner_name: str,username: str,room_name: str ,track: GetTrackSchema):
        user =  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        owner = UserRepository.get_user(owner_name)
        
        room = RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        tracks = RoomRepository.get_track_from_room(room_name,track)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found',
            )
        
        if owner.id == room.id:
            RoomRepository.del_track_from_room(user.id,track)
            return {'message': 'del track from room', 'detail': ''}


    @staticmethod
    def join_room(username: str, room_name: str, password: str | None = None):
        user = UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        room = RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.is_private:
            if not password:
                raise HTTPException(status_code=403, detail="Password required for this room")
            if not verify_pass(password, room.password_hash):
                raise HTTPException(status_code=403, detail="Invalid password")
            
        members = [member['username'] for member in RoomRepository.get_members_from_room(room_name)]

        if len(members) >= room.max_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Room is full'
            )

        RoomRepository.add_user_to_room(user.id, room.id)

        return {"message": "Joined room", "detail": room_name}
    

    @staticmethod
    def leave_room(username: str, room_name: str,):
        user = UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        room = RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        
        RoomRepository.del_user_from_room(user.id,room.id)
        return {'message': 'leave room', 'detail': room_name}
    

    @staticmethod
    def kick_member(owner_name: str,username: str, room_name: str):
        user = UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        owner = UserRepository.get_user(owner_name)
        

        room = RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        
        if owner.id == room.owner_id:
            RoomRepository.del_user_from_room(user.id,room.id)
            return {'message': 'leave room', 'detail': room_name}
        
    
    @staticmethod
    def ban_user_in_room(owner_name: str,username: str, room_name: str,ban_expired: datetime):
        user = UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        owner = UserRepository.get_user(owner_name)
        

        room = RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        existing_ban = RoomRepository.get_ban_for_user(user.id, room.id)
        if existing_ban:
            raise HTTPException(status_code=400, detail="User is already banned.")
        
        if owner.id == room.owner_id:
            RoomRepository.ban_user_in_room(user.id,room.id,ban_expired)
            return {'message': 'leave room', 'detail': room_name}
        
    
    @staticmethod
    def unban_user_in_room(owner_name: str,username: str, room_name: str):
        user = UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        owner = UserRepository.get_user(owner_name)
        

        room = RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        
        if owner.id == room.owner_id:
            RoomRepository.unban_user_in_room(user.id,room.id)
            return {'message': 'leave room', 'detail': room_name}
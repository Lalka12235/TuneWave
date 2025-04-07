from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.repositories.track_repo import TrackRepository

from app.schemas.track_schema import GetTrackSchema
from app.schemas.room_schema import RoomSchema, UpdRoomSchema

from fastapi import HTTPException,status

from app.utils.hash import make_hash_pass,verify_pass

from datetime import datetime

class RoomServices:

    @staticmethod
    async def get_room_on_name(name: str):
        room =await RoomRepository.get_room_on_name(name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        return {'message': 'get room on name','detail': room}
    
    
    @staticmethod
    async def get_all_room():
        rooms =await RoomRepository.get_all_room()

        if rooms is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='No one Rooms'
            )
        
        return {'message': 'get all rooms','detail': rooms}
    

    @staticmethod
    async def get_members_from_room(room_name: str):
        room =await RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        members = RoomRepository.get_members_from_room(room_name)

        return {'message': 'all members','detail': members}


    @staticmethod
    async def create_room(username: str,room_setting: RoomSchema):
        user =await  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        hash_pass = make_hash_pass(room_setting.password) if room_setting.private and room_setting.password else None
        
        room =await RoomRepository.create_room(user.id,room_setting.name,room_setting.max_member,room_setting.private,hash_pass)

        return {'message': 'create room','detail': room}
    

    @staticmethod
    async def update_room(username: str , upd_room: UpdRoomSchema):
        user = await UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        await RoomRepository.update_room(user.id,upd_room.name,upd_room.new_name,upd_room.max_member,upd_room.private)

        return {'message': 'update room','detail': ''}
    

    @staticmethod
    async def delete_room(username: str):
        user =await  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        await RoomRepository.delete_room(user.id)

        return {'message': 'delete room','detail': ''}
    

    @staticmethod
    async def set_current_track(room_name: str, track: GetTrackSchema):
        tracks =await TrackRepository.get_track(track)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        room =await RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )

        await RoomRepository.set_current_track(room.id,tracks.id)

        return {'message': 'set current track', 'detail': ''}


    @staticmethod
    async def get_current_track(room_name: str):
        room =await RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        await RoomRepository.get_current_track(room.id)

        return {'message': 'get current track', 'detail': ''}
    


    @staticmethod
    async def get_track_queue(room_name: str):
        room =await RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )

        queue =await RoomRepository.get_track_queue(room.id)

        return {'message': 'track queue', 'detail': queue}

    

    @staticmethod
    async def add_track_to_queue(username: str, room_name: str,track: GetTrackSchema):
        user =await  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        

        tracks =await TrackRepository.get_track(track)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found'
            )
        
        room =await RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        if user.id == room.owner_id:
            await RoomRepository.add_track_to_queue(user.id, track)
            return {'message': 'add track to room','detail': ''}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='None'
            )
    

    @staticmethod
    async def del_track_from_queue(username: str,room_name: str ,track: GetTrackSchema):
        user =await  UserRepository.get_user(username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        
        room = await RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        tracks =await RoomRepository.get_track_queue(room.id)

        if tracks is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found',
            )
        
        if user.id == room.owner_id:
            await RoomRepository.del_track_from_queue(room.id,track)
            return {'message': 'del track from room', 'detail': ''}
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='None'
            )


    @staticmethod
    async def skip_track_queue(room_name: str):
        room =await RoomRepository.get_room_on_name(room_name)

        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        await RoomRepository.skip_track_queue(room.id)

        return {'message': 'skip track','detail': ''}



    @staticmethod
    async def join_room(username: str, room_name: str, password: str | None = None):
        user =await UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        room =await RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.is_private:
            if not password:
                raise HTTPException(status_code=403, detail="Password required for this room")
            if not verify_pass(password, room.password_hash):
                raise HTTPException(status_code=403, detail="Invalid password")
            
        members = [member['username'] for member in await RoomRepository.get_members_from_room(room_name)]

        if len(members) >= room.max_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Room is full'
            )

        await RoomRepository.add_user_to_room(user.id, room.id)

        return {"message": "Joined room", "detail": room_name}
    

    @staticmethod
    async def leave_room(username: str, room_name: str,):
        user =await UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        room = RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        
        await RoomRepository.del_user_from_room(user.id,room.id)
        return {'message': 'leave room', 'detail': room_name}
    

    @staticmethod
    async def kick_member(owner_name: str,username: str, room_name: str):
        user =await UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        owner =await UserRepository.get_user(owner_name)
        

        room =await RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        
        if owner.id == room.owner_id:
            await RoomRepository.del_user_from_room(user.id,room.id)
            return {'message': 'leave room', 'detail': room_name}
        
    
    @staticmethod
    async def ban_user_in_room(owner_name: str,username: str, room_name: str,ban_expired: datetime):
        user =await UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        owner =await UserRepository.get_user(owner_name)
        

        room = await RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        existing_ban = await RoomRepository.get_ban_for_user(user.id, room.id)
        if existing_ban:
            raise HTTPException(status_code=400, detail="User is already banned.")
        
        if owner.id == room.owner_id:
            await RoomRepository.ban_user_in_room(user.id,room.id,ban_expired)
            return {'message': 'leave room', 'detail': room_name}
        
    
    @staticmethod
    async def unban_user_in_room(owner_name: str,username: str, room_name: str):
        user =await UserRepository.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        owner =await UserRepository.get_user(owner_name)
        

        room =await RoomRepository.get_room_on_name(room_name)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        
        if owner.id == room.owner_id:
            await RoomRepository.unban_user_in_room(user.id,room.id)
            return {'message': 'leave room', 'detail': room_name} 
        
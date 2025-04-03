from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository

from app.schemas.track_schema import GetTrackSchema

from fastapi import HTTPException,status



class RoomServices:

    @staticmethod
    def get_room_on_name(name: str):
        room = RoomRepository.get_room_on_name(name)

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        return {'message': 'get room on name','detail': room}
    
    
    @staticmethod
    def get_all_room():
        rooms = RoomRepository.get_all_room()

        if not rooms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='No one Rooms'
            )
        
        return {'message': 'get all rooms','detail': rooms}
    

    @staticmethod
    def get_members_from_room(room_name: str):
        room = RoomRepository.get_room_on_name(room_name)

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        members = RoomRepository.get_members_from_room(room_name)

        return {'message': 'all members','detail': members}


    @staticmethod
    def create_room(username: str,name: str, max_member: int, private: bool):
        user =  UserRepository.get_user(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        room = RoomRepository.create_room(user.id,name,max_member,private)

        return {'message': 'create room','detail': room}
    

    @staticmethod
    def update_room(username: str , name: str,new_name: str, max_member: int, private: bool):# кол-во учатстников и тип комнаты для обновление
        user =  UserRepository.get_user(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        upd_room = RoomRepository.update_room(user.id,name,new_name,max_member,private)

        return {'message': 'update room','detail': upd_room}
    

    @staticmethod
    def delete_room(username: str):
        user =  UserRepository.get_user(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        deL_room = RoomRepository.delete_room(user.id)

        return {'message': 'delete room','detail': deL_room}
    

    @staticmethod
    def add_track_to_room(username: str, room_name: str,track: GetTrackSchema):
        user =  UserRepository.get_user(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        room = RoomRepository.get_room_on_name(room_name)

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        add_track = RoomRepository.add_track_to_room(user.id, track)

        return {'message': 'add track to room','detail': add_track}
    

    @staticmethod
    def del_track_from_room(username: str,room_name: str ,track: GetTrackSchema):
        user =  UserRepository.get_user(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        room = RoomRepository.get_room_on_name(room_name)

        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found'
            )
        
        tracks = RoomRepository.get_track_from_room(room_name,track)

        if not tracks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Track not found',
            )
        
        result = RoomRepository.del_track_from_room(user.id,track)

        return {'message': 'del track from room', 'detail': result}


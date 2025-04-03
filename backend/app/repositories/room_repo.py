from sqlalchemy import select,insert,delete,update,and_
from app.config.session import Session
from app.models.room import RoomModel,RoomTracksModel,RoomMembersModel
from app.models.user import UserModel
from app.services.track_services import TrackServices
from app.schemas.track_schema import GetTrackSchema
from app.models.ban import BanModel
from datetime import datetime


class RoomRepository:
    
    @staticmethod
    def get_room_on_name(name: str):
        with Session() as session:
            stmt = select(RoomModel).where(RoomModel.name == name)
            result = session.execute(stmt).scalar_one_or_none()
            return result
        
        
    @staticmethod
    def get_all_room():
        with Session() as session:
            stmt = select(RoomModel)
            return session.execute(stmt).scalars().all()


    @staticmethod
    def get_members_from_room(room_name: str):
        with Session() as session:
            room = session.execute(select(RoomModel).where(RoomModel.name == room_name)).scalar_one_or_none()

            stmt = select(UserModel.id, UserModel.username).join(RoomMembersModel).where(RoomMembersModel.room_id == room.id)
            users = session.execute(stmt).all()
            
        return [{'username': user.username}for user in users]


    @staticmethod
    def create_room(user_id: int,name: str, max_members: int, private: bool, password_hash: str | None = None):
        with Session() as session:
            new_room = RoomModel(
                name=name,
                owner_id=user_id,
                max_members=max_members,
                is_private=private,
                password=password_hash,
            )

            member = RoomMembersModel(
                room_id=new_room.id,
                user_id=user_id,
                role='Admin'
            )

            session.add(new_room)
            session.add(member)
            session.commit()

            return new_room
    
    @staticmethod
    def update_room(user_id: int , name: str,new_name: str,max_member: int,private: bool):
        with Session() as session:
            upd_room = update(RoomModel).where(and_(
                RoomModel.name == name,
                RoomModel.owner_id == user_id,
            )).values(
                name=new_name,
                owner_id=user_id,
                max_member=max_member,
                is_private=private,
            )

            result = session.execute(upd_room)
            session.commit()
            return result
        
    
    @staticmethod
    def delete_room(user_id: str):
        with Session() as session:
            stmt = delete(RoomModel).where(RoomModel.owner_id == user_id)
            result = session.execute(stmt)

            return result
        

    @staticmethod
    def get_track_from_room(room_name: str, track: GetTrackSchema):
        with Session() as session:
            room = session.execute(select(RoomModel).where(RoomModel.name == room_name)).scalar_one_or_none()
            tracks = TrackServices.get_track(track)
            exist_track = session.execute(select(RoomTracksModel).where(and_(
                RoomTracksModel.track_id == tracks.id,
                RoomTracksModel.room_id == room.id,
                ))).scalar_one_or_none()
            return exist_track


        
    @staticmethod
    def add_track_to_room(user_id: int, track: GetTrackSchema):
        with Session() as session:
            room = session.execute(select(RoomModel).where(RoomModel.owner_id == user_id)).scalar_one_or_none()

            tracks = TrackServices.get_track(track)

            track_to_room = RoomTracksModel(
                room_id=room.id,
                track_id=tracks.id
            )

            session.add(track_to_room)
            session.commit()

            return track_to_room
        

    @staticmethod
    def del_track_from_room(user_id: int, track: GetTrackSchema):
        with Session() as session:
            room = session.execute(select(RoomModel).where(RoomModel.owner_id == user_id)).scalar_one_or_none()

            tracks = TrackServices.get_track(track)

            stmt= delete(RoomTracksModel).where(and_(
                RoomTracksModel.track_id == tracks.id,
                RoomModel.id == room.id,
                ))
            
            result = session.execute(stmt)
            session.commit()
            return result
        
        
    @staticmethod
    def add_user_to_room(user_id: int, room_id: int):
        with Session() as session:
            new_member = RoomMembersModel(user_id=user_id, room_id=room_id,role='Member')
            session.add(new_member)
            session.commit()


    @staticmethod
    def del_user_from_room(user_id: int, room_id: int):
        with Session() as session:
            stmt = delete(RoomMembersModel).where(RoomMembersModel.user_id == user_id, RoomMembersModel.room_id == room_id)
            result = session.execute(stmt)
            session.commit()
            return result
        
    
    @staticmethod
    def ban_user_in_room(user_id: int, room_id: int,ban_expired: datetime ,reason: str | None = None):
        with Session() as session:
            stmt = insert(BanModel).values(
                reason=reason,
                user_id=user_id,
                room_id=room_id,
                ban_expired=ban_expired
            )
            result = session.execute(stmt)
            session.commit()
            return result
        

    @staticmethod
    def unban_user_in_room(user_id: int, room_id: int,):
        with Session() as session:
            stmt = delete(BanModel).where(and_(
                BanModel.user_id==user_id,
                BanModel.room_id==room_id,
            ))
            result = session.execute(stmt)
            session.commit()
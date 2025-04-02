from sqlalchemy import select,insert,delete,update,and_
from app.config.session import Session
from app.models.room import RoomModel,RoomTracksModel,RoomMembersModel
from app.models.user import UserModel
from app.services.track_services import TrackServices
from app.schemas.track_schema import GetTrackSchema


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
    def create_room(user_id: int,name: str):# кол-во учатстников и тип комнаты для обновление
        with Session() as session:
            new_room = RoomModel(
                name=name,
                owner_id=user_id,
            )

            session.add(new_room)
            session.commit()

            return new_room
    
    @staticmethod
    def update_room(user_id: int , name: str,new_name: str): # кол-во учатстников и тип комнаты для обновление
        with Session() as session:
            upd_room = update(RoomModel).where(and_(
                RoomModel.name == name,
                RoomModel.owner_id == user_id,
            )).values(
                name=new_name,
                owner_id=user_id,
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
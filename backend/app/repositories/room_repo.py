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
            room = RoomRepository.get_room_on_name(room_name)

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
                cuurent_track_id=None,
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

            session.execute(upd_room)
            session.commit()
            return upd_room
        
    
    @staticmethod
    def delete_room(user_id: str):
        with Session() as session:
            stmt = delete(RoomModel).where(RoomModel.owner_id == user_id)
            session.execute(stmt)
        
    
    @staticmethod
    def set_current_track(room_id: int, track_id: int):
        with Session() as session:
            stmt = update(RoomModel).where(
                RoomModel.id == room_id,
            ).values(
                current_track_id=track_id,
            )
            session.execute(stmt)
            session.commit()

    
    @staticmethod
    def get_current_track(room_id):
        with Session() as session:
            stmt = select(RoomModel).where(RoomModel.id == room_id)
            result = session.execute(stmt).scalar_one_or_none()
            return result
        

    @staticmethod
    def get_track_queue(room_id: int):
        with Session() as session:
            stmt =  select(RoomTracksModel).where(RoomTracksModel.room_id == room_id).order_by(RoomTracksModel.position.asc())
            return session.execute(stmt).scalars()
        
            
        
    @staticmethod
    def add_track_to_queue(user_id: int, track: GetTrackSchema):
        with Session() as session:
            room = session.execute(select(RoomModel).where(RoomModel.owner_id == user_id)).scalar_one_or_none()

            tracks = TrackServices.get_track(track)

            max_position = session.execute(
                select(RoomTracksModel)
                .where(RoomTracksModel.room_id == room.id,)
                .order_by(RoomTracksModel.position.desc())
                .limit(1)
            ).scalar() or 0

            track_to_room = RoomTracksModel(
                room_id=room.id,
                track_id=tracks.id,
                position=max_position + 1
            )

            session.add(track_to_room)
            session.commit()
            return track_to_room
        

    @staticmethod
    def del_track_from_queue(room_id: int, track_id: int):
        with Session() as session:
            stmt= delete(RoomTracksModel).where(and_(
                RoomTracksModel.track_id == track_id,
                RoomTracksModel.id == room_id,
                ))
            
            session.execute(stmt)
            session.commit()


    @staticmethod
    def skip_track_queue(room_id: int):
        with Session() as session:
            queue = RoomRepository.get_track_queue(room_id)
            current_track = queue[0]

            session.delete(current_track)
            session.commit()

            if len(queue) > 1:
                next_track = queue[1]
                RoomRepository.set_current_track(room_id, next_track.track_id)
            else:
                RoomRepository.set_current_track(room_id,None)

            session.commit()

            
        
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
            session.execute(stmt)
            session.commit()
        

    @staticmethod
    def get_ban_for_user(user_id: int, room_id: int):
        with Session() as session:
            stmt = select(BanModel).where(and_(
                BanModel.user_id == user_id,
                BanModel.room_id == room_id,
                BanModel.ban_expired > datetime.now()
            ))
            return session.execute(stmt).scalar_one_or_none()

    
    @staticmethod
    def ban_user_in_room(user_id: int, room_id: int,ban_expired: datetime ,reason: str | None = None):
        with Session() as session:
            stmt = insert(BanModel).values(
                reason=reason,
                user_id=user_id,
                room_id=room_id,
                ban_expired=ban_expired
            )
            session.execute(stmt)
            session.commit()
        

    @staticmethod
    def unban_user_in_room(user_id: int, room_id: int,):
        with Session() as session:
            stmt = delete(BanModel).where(and_(
                BanModel.user_id==user_id,
                BanModel.room_id==room_id,
            ))
            session.execute(stmt)
            session.commit()


    @staticmethod
    def change_state_player(room_id: int, state: str):
        with Session() as session:
            stmt = update(RoomModel).where(RoomModel.id == room_id).values(player_state=state)
            session.execute(stmt)
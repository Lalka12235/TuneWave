from sqlalchemy import select,insert,delete,update,and_
from app.config.session import AsyncSessionLocal
from app.models.room import RoomModel,RoomTracksModel,RoomMembersModel
from app.models.user import UserModel
from app.services.track_services import TrackServices
from app.schemas.track_schema import GetTrackSchema
from app.models.ban import BanModel
from datetime import datetime


class RoomRepository:
    
    @staticmethod
    async def get_room_on_name(name: str):
        async with AsyncSessionLocal() as session:
            stmt = select(RoomModel).where(RoomModel.name == name)
            result = await session.execute(stmt).scalar_one_or_none()
            return result
        
        
    @staticmethod
    async def get_all_room():
        async with AsyncSessionLocal() as session:
            stmt = select(RoomModel)
            return await session.execute(stmt).scalars().all()


    @staticmethod
    async def get_members_from_room(room_name: str):
        async with AsyncSessionLocal() as session:
            room = RoomRepository.get_room_on_name(room_name)

            stmt = select(UserModel.id, UserModel.username).join(RoomMembersModel).where(RoomMembersModel.room_id == room.id)
            users = await session.execute(stmt).all()
            
        return [{'username': user.username}for user in users]


    @staticmethod
    async def create_room(user_id: int,name: str, max_members: int, private: bool, password_hash: str | None = None):
        async with AsyncSessionLocal() as session:
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
            await session.commit()

            return new_room
    
    @staticmethod
    async def update_room(user_id: int , name: str,new_name: str,max_member: int,private: bool):
        async with AsyncSessionLocal() as session:
            upd_room = update(RoomModel).where(and_(
                RoomModel.name == name,
                RoomModel.owner_id == user_id,
            )).values(
                name=new_name,
                owner_id=user_id,
                max_member=max_member,
                is_private=private,
            )

            await session.execute(upd_room)
            await session.commit()
            return upd_room
        
    
    @staticmethod
    async def delete_room(user_id: str):
        async with AsyncSessionLocal() as session:
            stmt = delete(RoomModel).where(RoomModel.owner_id == user_id)
            await session.execute(stmt)
        
    
    @staticmethod
    async def set_current_track(room_id: int, track_id: int):
        async with AsyncSessionLocal() as session:
            stmt = update(RoomModel).where(
                RoomModel.id == room_id,
            ).values(
                current_track_id=track_id,
            )
            await session.execute(stmt)
            await session.commit()

    
    @staticmethod
    async def get_current_track(room_id):
        async with AsyncSessionLocal() as session:
            stmt = select(RoomModel).where(RoomModel.id == room_id)
            result = await session.execute(stmt).scalar_one_or_none()
            return result
        

    @staticmethod
    async def get_track_queue(room_id: int):
        async with AsyncSessionLocal() as session:
            stmt =  select(RoomTracksModel).where(RoomTracksModel.room_id == room_id).order_by(RoomTracksModel.position.asc())
            return await session.execute(stmt).scalars()
        
            
        
    @staticmethod
    async def add_track_to_queue(user_id: int, track: GetTrackSchema):
        async with AsyncSessionLocal() as session:
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
            await session.commit()
            return track_to_room
        

    @staticmethod
    async def del_track_from_queue(room_id: int, track_id: int):
        async with AsyncSessionLocal() as session:
            stmt= delete(RoomTracksModel).where(and_(
                RoomTracksModel.track_id == track_id,
                RoomTracksModel.id == room_id,
                ))
            
            await session.execute(stmt)
            await session.commit()


    @staticmethod
    async def skip_track_queue(room_id: int):
        async with AsyncSessionLocal() as session:
            queue = RoomRepository.get_track_queue(room_id)
            current_track = queue[0]

            await session.delete(current_track)
            await session.commit()

            if len(queue) > 1:
                next_track = queue[1]
                RoomRepository.set_current_track(room_id, next_track.track_id)
            else:
                RoomRepository.set_current_track(room_id,None)

            await session.commit()

            
        
    @staticmethod
    async def add_user_to_room(user_id: int, room_id: int):
        async with AsyncSessionLocal() as session:
            new_member = RoomMembersModel(user_id=user_id, room_id=room_id,role='Member')
            session.add(new_member)
            await session.commit()


    @staticmethod
    async def del_user_from_room(user_id: int, room_id: int):
        async with AsyncSessionLocal() as session:
            stmt = delete(RoomMembersModel).where(RoomMembersModel.user_id == user_id, RoomMembersModel.room_id == room_id)
            await session.execute(stmt)
            await session.commit()
        

    @staticmethod
    async def get_ban_for_user(user_id: int, room_id: int):
        async with AsyncSessionLocal() as session:
            stmt = select(BanModel).where(and_(
                BanModel.user_id == user_id,
                BanModel.room_id == room_id,
                BanModel.ban_expired > datetime.now()
            ))
            return await session.execute(stmt).scalar_one_or_none()

    
    @staticmethod
    async def ban_user_in_room(user_id: int, room_id: int,ban_expired: datetime ,reason: str | None = None):
        async with AsyncSessionLocal() as session:
            stmt = insert(BanModel).values(
                reason=reason,
                user_id=user_id,
                room_id=room_id,
                ban_expired=ban_expired
            )
            await session.execute(stmt)
            await session.commit()
        

    @staticmethod
    async def unban_user_in_room(user_id: int, room_id: int,):
        async with AsyncSessionLocal() as session:
            stmt = delete(BanModel).where(and_(
                BanModel.user_id==user_id,
                BanModel.room_id==room_id,
            ))
            await session.execute(stmt)
            await session.commit()


    @staticmethod
    async def change_state_player(room_id: int, state: str):
        async with AsyncSessionLocal() as session:
            stmt = update(RoomModel).where(RoomModel.id == room_id).values(player_state=state)
            await session.execute(stmt)
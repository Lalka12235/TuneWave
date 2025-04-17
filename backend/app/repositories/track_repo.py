from sqlalchemy import select,insert,delete,update,and_
from app.config.session import AsyncSessionLocal
from backend.app.schemas.track_schema import (
    TrackSchema,
    GetTrackSchema,
    UpdateTrackSchema, 
    DeleteTrackSchema)
from app.models.track import TrackModel

import logging

logger = logging.getLogger(__name__)



class TrackRepository:

    @staticmethod
    async def get_track(track: GetTrackSchema):
        async with AsyncSessionLocal() as session:
            
            stmt =  select(TrackModel).where(
                TrackModel.title == track.title,
                TrackModel.artist == track.artist,
            )
            result = await session.execute(stmt).scalar_one_or_none()
            return result
        
    @staticmethod
    async def create_track(track: TrackSchema,user_id: int):
        async with AsyncSessionLocal() as session:
            new_track = TrackModel(
                title=track.title,
                artist=track.artist,
                genre=track.genre,
                url=track.url,
                user_id=user_id,
            )

            await session.add(new_track)
            await session.commit()

            return new_track
        
    @staticmethod
    async def update_track(upd_track: UpdateTrackSchema):
        async with AsyncSessionLocal() as session:
            stmt = update(TrackModel).where(and_(
                TrackModel.title == upd_track.title,
                TrackModel.artist == upd_track.artist,
            )).values(title=upd_track.title,artist=upd_track.artist)
            result = await session.execute(stmt)
            await session.commit()

            return result
        
    
    @staticmethod
    async def delete_track(user_id: int,del_track: DeleteTrackSchema):
        async with AsyncSessionLocal() as session:
            stmt = delete(TrackModel).where(and_(
                TrackModel.title == del_track.title,
                TrackModel.artist == del_track.artist,
                TrackModel.user_id == user_id
            ))

            await session.execute(stmt)
            await session.commit()
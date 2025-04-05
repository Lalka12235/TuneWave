from sqlalchemy import select,insert,delete,update,and_
from app.config.session import Session
from backend.app.schemas.track_schema import (
    TrackSchema,
    GetTrackSchema,
    UpdateTrackSchema, 
    DeleteTrackSchema)
from app.models.track import TrackModel



class TrackRepository:

    @staticmethod
    def get_track(track: GetTrackSchema):
        with Session() as session:
            stmt =  select(TrackModel).where(
                TrackModel.title == track.title,
                TrackModel.artist == track.artist,
            )
            result = session.execute(stmt).scalar_one_or_none()
            return result
        
    @staticmethod
    def create_track(track: TrackSchema,user_id: int):
        with Session() as session:
            new_track = TrackModel(
                title=track.title,
                artist=track.artist,
                genre=track.genre,
                url=track.url,
                user_id=user_id,
            )

            session.add(new_track)
            session.commit()

            return new_track
        
    @staticmethod
    def update_track(upd_track: UpdateTrackSchema):
        with Session() as session:
            stmt = update(TrackModel).where(and_(
                TrackModel.title == upd_track.title,
                TrackModel.artist == upd_track.artist,
            )).values(title=upd_track.title,artist=upd_track.artist)
            result = session.execute(stmt)
            session.commit()

            return result
        
    
    @staticmethod
    def delete_track(user_id: int,del_track: DeleteTrackSchema):
        with Session() as session:
            stmt = delete(TrackModel).where(and_(
                TrackModel.title == del_track.title,
                TrackModel.artist == del_track.artist,
                TrackModel.user_id == user_id
            ))

            session.execute(stmt)
            session.commit()
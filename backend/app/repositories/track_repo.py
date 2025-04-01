from sqlalchemy import select,insert,delete,update
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
            result = session.execute(stmt).scalar_one_or_none
            return result
        
    @staticmethod
    def create_track(track: TrackSchema):
        with Session() as session:
            new_track = TrackSchema(
                title=track.title,
                artist=track.artist,
                genre=track.genre,
                url=track.url,
            )

            session.add(new_track)
            session.commit()

            return True
        
    @staticmethod
    def update_track(upd_track: UpdateTrackSchema):
        with Session() as session:
            stmt = update(TrackModel).where(
                TrackModel.title == upd_track.title,
                TrackModel.artist == upd_track.artist,
            )
            result = session.execute(stmt)
            session.commit()

            return result
        
    
    @staticmethod
    def delete_track(del_track: DeleteTrackSchema):
        with Session() as session:
            stmt = delete(TrackModel).where(
                TrackModel.title == del_track.title,
                TrackModel.artist == del_track.artist,
            )

            result = session.execute(stmt)
            session.commit()

            return result
        

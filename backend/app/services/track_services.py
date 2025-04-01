from app.repositories.track_repo import TrackRepository
from backend.app.schemas.track_schema import (
    TrackSchema,
    GetTrackSchema,
    UpdateTrackSchema, 
    DeleteTrackSchema
)
from fastapi import HTTPException, status


class TrackServices:

    @staticmethod
    def 
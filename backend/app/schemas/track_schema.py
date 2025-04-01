from pydantic import BaseModel

class TrackSchema(BaseModel):
    title: str
    artist: str
    genre: str
    url: str

class GetTrackSchema(BaseModel):
    title:str
    artist:str

class UpdateTrackSchema(BaseModel):
    title: str
    artist: str

class DeleteTrackSchema(UpdateTrackSchema):
    pass
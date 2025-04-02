from pydantic import BaseModel, Field

class RoomSchema(BaseModel):
    name: str
    member: int = Field(max_digits=4)


class RoomTracksSchemas(BaseModel):
    pass

class RoomMemberSchema(BaseModel):
    role: str
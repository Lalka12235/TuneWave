from pydantic import BaseModel, Field

class RoomSchema(BaseModel):
    name: str
    max_member: int = Field(max_digits=4)
    private: bool | None = Field(default=None)
    password: str | None = Field(default=None)


class UpdRoomSchema(RoomSchema):
    new_name: str

class RoomTracksSchemas(BaseModel):
    pass

class RoomMemberSchema(BaseModel):
    role: str
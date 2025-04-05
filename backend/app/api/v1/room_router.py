from fastapi import APIRouter, Query
from typing import Annotated
from datetime import datetime

from app.services.room_services import RoomServices
from app.schemas.room_schema import RoomSchema, UpdRoomSchema
from app.schemas.track_schema import GetTrackSchema

room = APIRouter(tags=["Room"])


# 🎧 Room CRUD
@room.get("/room")
async def get_all_rooms():
    return RoomServices.get_all_room()

@room.get("/room/{room_name}")
async def get_room_by_name(room_name: str):
    return RoomServices.get_room_on_name(room_name)

@room.post("/room")
async def create_room(username: Annotated[str, Query()], room_settings: RoomSchema):
    return RoomServices.create_room(username, room_settings)

@room.put("/room/{room_name}")
async def update_room(username: Annotated[str, Query()], room_name: str, room_settings: UpdRoomSchema):
    return RoomServices.update_room(username, room_settings)

@room.delete("/room/{username}")
async def delete_room(username: str):
    return RoomServices.delete_room(username)


# 👥 Members
@room.get("/room/{room_name}/members")
async def get_members_from_room(room_name: str):
    return RoomServices.get_members_from_room(room_name)

@room.post("/room/{room_name}/join")
async def join_room(username: Annotated[str, Query()], room_name: str, password: Annotated[str | None, Query()] = None):
    return RoomServices.join_room(username, room_name, password)

@room.post("/room/{room_name}/leave")
async def leave_room(username: Annotated[str, Query()], room_name: str):
    return RoomServices.leave_room(username, room_name)

@room.post("/room/{room_name}/kick")
async def kick_member(owner_name: Annotated[str, Query()], username: Annotated[str, Query()], room_name: str):
    return RoomServices.kick_member(owner_name, username, room_name)

@room.post("/room/{room_name}/ban")
async def ban_user_in_room(
    owner_name: Annotated[str, Query()],
    username: Annotated[str, Query()],
    room_name: str,
    ban_expired: Annotated[datetime, Query()],
):
    return RoomServices.ban_user_in_room(owner_name, username, room_name, ban_expired)

@room.delete("/room/{room_name}/ban")
async def unban_user_in_room(
    owner_name: Annotated[str, Query()],
    username: Annotated[str, Query()],
    room_name: str,
):
    return RoomServices.unban_user_in_room(owner_name, username, room_name)


# 🎵 Current track
@room.get("/room/{room_name}/track")
async def get_current_track(room_name: str):
    return RoomServices.get_current_track(room_name)

@room.post("/room/{room_name}/track")
async def set_current_track(room_name: str, track: GetTrackSchema):
    return RoomServices.set_current_track(room_name, track)


# 📃 Queue 
@room.post("/room/{room_name}/queue")
async def add_track_to_queue(username: Annotated[str, Query()], room_name: str, track: GetTrackSchema):
    return RoomServices.add_track_to_queue(username, room_name, track)

@room.delete("/room/{room_name}/queue")
async def del_track_from_queue(username: Annotated[str, Query()], room_name: str, track: GetTrackSchema):
    return RoomServices.del_track_from_queue(username, room_name, track)

@room.post("/room/{room_name}/queue/skip")
async def skip_track_queue(room_name: str):
    return RoomServices.skip_track_queue(room_name)

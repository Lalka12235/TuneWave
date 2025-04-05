from fastapi import APIRouter

from app.services.player_services import PlayerService



player = APIRouter(tags=['Player'])


@player.post('/room/{room_name}/player/start')
async def start_track(room_name: str):
    return PlayerService.start_track(room_name)


@player.post('/room/{room_name}/player/pause')
async def pause_track(room_name: str):
    return PlayerService.pause_track(room_name)


@player.post('/room/{room_name}/player/skip')
async def skip_track(room_name: str):
    return PlayerService.skip_track(room_name)
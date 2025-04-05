from fastapi import APIRouter,Depends

from app.services.player_services import PlayerService

from app.auth.auth import get_current_user,check_authorization

player = APIRouter(tags=['Player'])


@player.post('/room/{room_name}/player/start')
async def start_track(room_name: str,current_user: str = Depends(get_current_user), _ = Depends(check_authorization)):
    return PlayerService.start_track(room_name)


@player.post('/room/{room_name}/player/pause')
async def pause_track(room_name: str,current_user: str = Depends(get_current_user), _ = Depends(check_authorization)):
    return PlayerService.pause_track(room_name)


@player.post('/room/{room_name}/player/skip')
async def skip_track(room_name: str,current_user: str = Depends(get_current_user), _ = Depends(check_authorization)):
    return PlayerService.skip_track(room_name)
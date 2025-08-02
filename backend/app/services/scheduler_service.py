from app.config.session import get_db
from app.services.room_service import RoomService
from app.repositories.room_repo import RoomRepository
from app.repositories.room_track_association_repo import RoomTrackAssociationRepository

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.spotify_sevice import SpotifyService


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.room_service = RoomService()

    def start(self):
        """
        Запускает планировщик и добавляет задачу.
        """
        # Добавляем задачу, которая будет выполняться каждые 5 секунд
        self.scheduler.add_job(
            self._check_rooms_for_playback,
            trigger=IntervalTrigger(seconds=5),
            id='check_rooms_playback_job',
            name='Check Rooms Playback Status'
        )
        self.scheduler.start()

    async def _check_rooms_for_playback(self):
        """
        Фоновая задача, которая проверяет статус воспроизведения в каждой комнате.
        """ 
        db = next(get_db())
        try:
            active_rooms = RoomRepository.get_active_rooms(db)

            for room in active_rooms:
                if room.current_track_id and room.is_playing:
                    owner_user = RoomRepository.get_owner_room(db, room.id)
                    if not owner_user or not owner_user.spotify_access_token:
                        continue

                    spotify = SpotifyService(db,owner_user)


                    try:
                        device_id = await spotify._get_device_id(owner_user.spotify_access_token)
                        if not device_id:
                            continue
                        state = await spotify.get_playback_state()
                        time_left = state.get('duration_ms') - state.get('progress_ms')
                        if time_left <= 5000:
                            next_track_association = RoomTrackAssociationRepository.get_first_track_in_queue(db, room.id)
                        
                            if next_track_association:
                                await spotify.play(
                                    access_token=owner_user.spotify_access_token,
                                    track_uri=next_track_association.track.spotify_uri,
                                    device_id=device_id
                                )
                            
                            room.current_track_id = next_track_association.track_id
                            room.current_track_position_ms = 0
                            
                            RoomTrackAssociationRepository.remove_track_from_queue_by_association_id(db, next_track_association.id)
                            RoomService._reorder_queue(db, room.id)
                        else:
                            await spotify.pause(device_id=device_id)
                            room.is_playing = False
                            room.current_track_id = None
                            db.commit()
                    except Exception as e:
                        try:
                            await spotify.pause(device_id=device_id)
                        except:
                            pass                  
        finally:
            db.close()
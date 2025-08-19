from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.loggingMiddleware import LogMiddleware
from app.api.v1.auth_api import auth
from app.api.v1.user_api import user
from app.api.v1.room_api import room
from app.api.v1.spotify_api import spotify
from app.api.v1.spotify_public_api import spotify_public
from app.api.v1.track_api import track
from app.api.v1.ws_chat_api import chat_ws
from app.api.v1.chat_api import chat
from app.api.v1.favorite_track_api import ft
from app.logger.log_config import configure_logging
from app.services.scheduler_service import SchedulerService
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from app.config.settings import settings
import os

configure_logging()

app = FastAPI(
    title="TuneWave",
    description="""
    🎵 **TuneWave** - Ваша персональная музыкальная вселенная
    
    ✨ **Ключевые возможности:**
    - 🎧 Умное управление трек-коллекцией
    - 📁 Организация плейлистов с душой
    - 🔗 Легкий обмен музыкой с друзьями
    - 🌐 Доступ к вашей музыке из любой точки мира
    
    🚀 Откройте новый уровень взаимодействия с музыкой!
    """,
    version="1.0.0",
    contact={
        "name": "Egor",
        "url": "https://github.com/Lalka12235",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[{
        "name": "music",
        "description": "Операции с музыкальными треками"
    }],
)

scheduler_service = SchedulerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    """
    os.makedirs(settings.AVATARS_STORAGE_DIR,exist_ok=True)
    scheduler_service.start()
    r = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)
    
    yield  # Здесь приложение начинает обрабатывать запросы

    scheduler_service.scheduler.shutdown()


@app.get('/ping')
async def ping():
    return 'Server is running'


#origins = [
#    "http://localhost",  
#    "http://localhost:8080",
#    "http://127.0.0.1:5500",#test
#]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

app.add_middleware(LogMiddleware)

app.include_router(auth)
app.include_router(user)
app.include_router(room)
app.include_router(spotify)
#app.include_router(ws)
app.include_router(spotify_public)
app.include_router(track)
app.include_router(chat_ws)
app.include_router(chat)
app.include_router(ft)

app.mount("/avatars", StaticFiles(directory=settings.AVATARS_STORAGE_DIR), name="avatars")
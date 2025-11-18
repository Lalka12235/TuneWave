from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.loggingMiddleware import LogMiddleware
from app.presentation.api.v1.all_route import V1_ROUTERS
from app.config.log_config import configure_logging
#from app.application.services.scheduler_service import SchedulerService
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from app.config.settings import settings
import os
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.presentation.api.v1.error_handler import register_errors_handlers

from dishka.integrations.fastapi import setup_dishka
from app.config.di.container import get_container

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    """
    #scheduler_service.start()
    r = redis.from_url(settings.redis.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)
    
    yield

    #scheduler_service.scheduler.shutdown()

    await r.close()

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
    lifespan=lifespan
)

#scheduler_service = SchedulerService()
app.add_middleware(ProxyHeadersMiddleware)

container = get_container()
setup_dishka(container,app)


@app.get('/ping')
async def ping():
    return 'Server is running'


#origins = [
#    "http://localhost",  
#    "http://localhost:8080",
#]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

app.add_middleware(LogMiddleware)
register_errors_handlers(app)

for route in V1_ROUTERS:
    app.include_router(route)

os.makedirs(settings.avatar.AVATARS_STORAGE_DIR,exist_ok=True)
app.mount("/avatars", StaticFiles(directory=settings.avatar.AVATARS_STORAGE_DIR), name="avatars")
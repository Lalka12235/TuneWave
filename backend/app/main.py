from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.loggingMiddleware import LogMiddleware
from app.api.v1.all_route import V1_ROUTERS
from app.logger.log_config import configure_logging
from app.services.scheduler_service import SchedulerService
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from app.config.settings import settings
import os
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    """
    scheduler_service.start()
    r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)
    
    yield

    scheduler_service.scheduler.shutdown()

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

scheduler_service = SchedulerService()
app.add_middleware(ProxyHeadersMiddleware)



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

for route in V1_ROUTERS:
    app.include_router(route)

os.makedirs(settings.AVATARS_STORAGE_DIR,exist_ok=True)
app.mount("/avatars", StaticFiles(directory=settings.AVATARS_STORAGE_DIR), name="avatars")
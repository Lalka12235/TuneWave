from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import os

from app.presentation.middleware.loggingMiddleware import LogMiddleware
from app.presentation.middleware.session_middleware import SessionMiddleware
from app.presentation.api.v1.all_route import V1_ROUTERS
from app.config.log_config import configure_logging
from app.config.settings import settings
from app.presentation.api.v1.error_handler import register_errors_handlers
import uvicorn
import multiprocessing

from dishka.integrations.fastapi import setup_dishka
from app.infrastructure.di.container import get_container

configure_logging()


def setup_router(app: FastAPI, routers: list):
    @app.get('/ping')
    async def ping():
        return 'Server is running'
    for route in routers:
        app.include_router(route)


def create_app() -> FastAPI:
    app = FastAPI( title="TuneWave",
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
        # lifespan=lifespan
    )

    app.add_middleware(ProxyHeadersMiddleware)
    

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LogMiddleware)
    app.add_middleware(SessionMiddleware)

    register_errors_handlers(app)

    setup_router(app, V1_ROUTERS)
    setup_dishka(get_container,app)
    
    os.makedirs(settings.avatar.AVATARS_STORAGE_DIR, exist_ok=True)
    app.mount("/avatars", StaticFiles(directory=settings.avatar.AVATARS_STORAGE_DIR), name="avatars")

    return app

app = create_app()



if __name__ == "__main__":
    uvicorn.run(app,reload=True,workers=multiprocessing.cpu_count(),host='0.0.0.0',port=8000,factory=True)

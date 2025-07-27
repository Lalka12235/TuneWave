from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.loggingMiddleware import LogMiddleware
from app.api.v1.auth_api import auth
from app.api.v1.user_api import user
from app.api.v1.room_api import room
from app.logger.log_config import configure_logging

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

@app.get('/ping')
async def ping():
    return 'Server is running'

origins = [
    "http://localhost",  
    "http://localhost:8080",
    "http://127.0.0.1:5500",#test
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

app.add_middleware(LogMiddleware)

app.include_router(auth)
app.include_router(user)
app.include_router(room)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.player_router import player
from app.api.v1.room_router import room
from app.api.v1.track_router import track
from app.api.v1.user_router import user
from app.api.v1.ws_router import ws

from app.logger.log_config import configure_logging

from app.config.loggingMiddleware import LogMiddleware
import logging
#from app.config.cspmiddleware import csp_middleware

configure_logging()
logging.getLogger("watchfiles").setLevel(logging.WARNING)

app = FastAPI(
    title='TuneWave',
    description='Trackify - is your personal music collection where every track and playlist has its place. Easily add, \
        update and share music with friends. Manage your music world wherever you are.'
)

@app.get('/ping')
async def ping():
    return 'Server is running'

origins = [
    "http://localhost",  
    "http://localhost:8080",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

app.add_middleware(LogMiddleware)
#app.add_middleware(csp_middleware)


app.include_router(user)
app.include_router(track)
app.include_router(room)
app.include_router(player)
app.include_router(ws)
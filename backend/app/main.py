from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.player_router import player
from app.api.v1.room_router import room
from app.api.v1.track_router import track
from app.api.v1.user_router import user

app = FastAPI(
    title='TuneWave',
    description='Trackify - is your personal music collection where every track and playlist has its place. Easily add, \
        update and share music with friends. Manage your music world wherever you are.'
)


origins = [
    "http://localhost",  
    "http://localhost:3000",  
    "https://yourdomain.com", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)


app.include_router(user)
app.include_router(track)
app.include_router(room)
app.include_router(player)
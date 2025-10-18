from app.api.v1.auth_api import auth
from app.api.v1.user_api import user
from app.api.v1.room_api import room
from app.api.v1.spotify_api import spotify
from app.api.v1.spotify_public_api import spotify_public
from app.api.v1.track_api import track
from app.api.v1.ws_chat_api import chat_ws
from app.api.v1.chat_api import chat
from app.api.v1.favorite_track_api import ft
from app.api.v1.friendship_api import friendship
from app.api.v1.ban_api import ban
from app.api.v1.notification_api import notification
from app.api.v1.ws_api import ws

V1_ROUTERS = [auth,user,room,spotify,spotify_public,track,chat_ws,chat,ft,friendship,ban,notification,ws]
from app.presentation.api.v1.auth_api import auth
from app.presentation.api.v1.ban_api import ban
from app.presentation.api.v1.chat_api import chat
from app.presentation.api.v1.favorite_track_api import ft
from app.presentation.api.v1.friendship_api import friendship
from app.presentation.api.v1.notification_api import notification
from app.presentation.api.v1.room_api import room
from app.presentation.api.v1.spotify_api import spotify
from app.presentation.api.v1.spotify_public_api import spotify_public
from app.presentation.api.v1.track_api import track
from app.presentation.api.v1.user_api import user
from app.presentation.api.v1.ws_api import ws
from app.presentation.api.v1.ws_chat_api import chat_ws
from app.presentation.api.v1.room_member_api import room_member
from app.presentation.api.v1.room_playback_api import room_playback
from app.presentation.api.v1.room_queue_api import room_queue

V1_ROUTERS = [auth,user,room,spotify,spotify_public,track,chat_ws,chat,ft,friendship,ban,notification,ws,room_member,room_playback,room_queue]
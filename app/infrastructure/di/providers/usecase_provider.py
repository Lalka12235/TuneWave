from dishka import Provider,Scope,provide_all
from app.application.commands.user import CreateUser,UpdateUser,DeleteUser,ReadUser
from app.application.commands.track import CreateTrack,ReadTrack,DeleteTrack
from app.application.commands.avatar import LoadAvatar
from app.application.commands.ban import ReadBan,CreateBan,RemoveBan
from app.application.commands.chat import MessageCreate,ReadMessage
from app.application.commands.favorite_track import ReadFavoriteTrack,DeleteFavoriteTrack,CreateTrackFavorite
from app.application.commands.friendship import ReadFriendship,SendFriendRequest,AcceptFriendRequest,DeleteFreidnship,DeclineFriendRequest
from app.application.commands.notification import ReadNotification,CreateNotification,DeleteNotification,MarkReadNotification
from app.application.commands.room import ReadRoom,CreateRoom,DeleteRoom,UpdateRoom
from app.application.commands.room_member import JoinRoom,ReadMember,SendRoomInvite,LeaveRoom,HandleRoomInvite,BanUserInRoom,UnbanUserInRoom,UpdateMemberRole
from app.application.commands.room_playback import PlayerPause,PlayerPlay,PlayerPrevious,PlayerSkip,SetPlaybackHost,ReadPlayerState,ClearPlaybackState,UpdateRoomPlaybackState
from app.application.commands.room_queue import ReadRoomQueue,RemoveTrackFromQueue,AddTrackRoomQueue


class UseCaseProvider(Provider):
    scope = Scope.REQUEST

    interactors = provide_all(
        #user
        CreateUser,
        UpdateUser,
        DeleteUser,
        ReadUser,
        #track
        CreateTrack,
        ReadTrack,
        DeleteTrack,
        #avatar
        LoadAvatar,
        #ban
        ReadBan,
        CreateBan,
        RemoveBan,
        #favorite track
        ReadFavoriteTrack,
        DeleteFavoriteTrack,
        CreateTrackFavorite,
        #friendship
        ReadFriendship,
        SendFriendRequest,
        AcceptFriendRequest,
        DeleteFreidnship,
        DeclineFriendRequest,
        #notification
        ReadNotification,
        CreateNotification,
        DeleteNotification,
        MarkReadNotification,
        #room
        ReadRoom,
        CreateRoom,
        DeleteRoom,
        UpdateRoom,
        #room member
        JoinRoom,
        ReadMember,
        SendRoomInvite,
        LeaveRoom,
        HandleRoomInvite,
        BanUserInRoom,
        UnbanUserInRoom,
        UpdateMemberRole,
        #room playback
        PlayerPause,
        PlayerPlay,
        PlayerPrevious,
        PlayerSkip,
        SetPlaybackHost,
        ReadPlayerState,
        ClearPlaybackState,
        UpdateRoomPlaybackState,
        #room queue
        ReadRoomQueue,
        RemoveTrackFromQueue,
        AddTrackRoomQueue,
        MessageCreate,
        ReadMessage,
    )
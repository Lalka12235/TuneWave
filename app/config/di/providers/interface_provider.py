from dishka import Provider,Scope,provide_all

from app.domain.interfaces.ban_repo import BanRepository
from app.domain.interfaces.chat_repo import ChatRepository
from app.domain.interfaces.track_repo import TrackRepository
from app.domain.interfaces.user_repo import UserRepository
from app.domain.interfaces.member_room_association import MemberRoomAssociationRepository
from app.domain.interfaces.notification_repo import NotificationRepository
from app.domain.interfaces.room_repo import RoomRepository
from app.domain.interfaces.room_track_association_repo import RoomTrackAssociationRepository
from app.domain.interfaces.favorite_track_repo import FavoriteTrackRepository
from app.domain.interfaces.friendship_repo import FriendshipRepository


class InterfaceProvider(Provider):
    scope = Scope.REQUEST

    interfaces = provide_all(
        BanRepository,
        ChatRepository,
        TrackRepository,
        UserRepository,
        MemberRoomAssociationRepository,
        NotificationRepository,
        RoomRepository,
        RoomTrackAssociationRepository,
        FavoriteTrackRepository,
        FriendshipRepository
    )


def interface_provider() -> InterfaceProvider:
    return InterfaceProvider()
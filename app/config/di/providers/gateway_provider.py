from dishka import Provider, Scope,WithParents, provide_all

from app.infrastructure.db.gateway.user_gateway import SAUserGateway
from app.infrastructure.db.gateway.ban_gateway import SABanGateway
from app.infrastructure.db.gateway.chat_gateway import SAChatGateway
from app.infrastructure.db.gateway.favorite_track_gateway import SAFavoriteTrackGateway
from app.infrastructure.db.gateway.friendship_gateway import SAFriendshipGateway
from app.infrastructure.db.gateway.member_room_association_gateway import SAMemberRoomAssociationGateway
from app.infrastructure.db.gateway.notification_gateway import SANotificationGateway
from app.infrastructure.db.gateway.room_gateway import SARoomGateway
from app.infrastructure.db.gateway.track_gateway import SATrackGateway
from app.infrastructure.db.gateway.room_track_association_gateway import SARoomTrackAssociationGateway


class GatewayProvider(Provider):
    scope = Scope.REQUEST

    repositories = provide_all(
        WithParents[SAUserGateway],
        WithParents[SABanGateway],
        WithParents[SAChatGateway],
        WithParents[SAFavoriteTrackGateway],
        WithParents[SAFriendshipGateway],
        WithParents[SAMemberRoomAssociationGateway],
        WithParents[SANotificationGateway],
        WithParents[SARoomGateway],
        WithParents[SATrackGateway],
        WithParents[SARoomTrackAssociationGateway],
    )
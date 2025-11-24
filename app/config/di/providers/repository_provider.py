from dishka import Provider, Scope,WithParents, provide_all

from app.infrastructure.db.repositories.user_repo import SQLalchemyUserRepository
from app.infrastructure.db.repositories.ban_repo import SQLalchemyBanRepository
from app.infrastructure.db.repositories.chat_repo import SQLalchemyChatRepository
from app.infrastructure.db.repositories.favorite_track_repo import SQLalchemyFavoriteTrackRepository
from app.infrastructure.db.repositories.friendship_repo import SQLalchemyFriendshipRepository
from app.infrastructure.db.repositories.member_room_association_repo import SQLalchemyMemberRoomAssociationRepository
from app.infrastructure.db.repositories.notification_repo import SQLalchemyNotificationRepository
from app.infrastructure.db.repositories.room_repo import SQLalchemyRoomRepository
from app.infrastructure.db.repositories.track_repo import SQLalchemyTrackRepository
from app.infrastructure.db.repositories.room_track_association_repo import SQLalchemyRoomTrackAssociationRepository


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    repositories = provide_all(
        WithParents[SQLalchemyUserRepository],
        WithParents[SQLalchemyBanRepository],
        WithParents[SQLalchemyChatRepository],
        WithParents[SQLalchemyFavoriteTrackRepository],
        WithParents[SQLalchemyFriendshipRepository],
        WithParents[SQLalchemyMemberRoomAssociationRepository],
        WithParents[SQLalchemyNotificationRepository],
        WithParents[SQLalchemyRoomRepository],
        WithParents[SQLalchemyTrackRepository],
        WithParents[SQLalchemyRoomTrackAssociationRepository],
    )
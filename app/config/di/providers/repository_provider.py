from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

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

    db: Session

    @provide
    def user_repo(self, db: Session) -> SQLalchemyUserRepository:
        return SQLalchemyUserRepository(db)

    @provide
    def ban_repo(self, db: Session) -> SQLalchemyBanRepository:
        return SQLalchemyBanRepository(db)

    @provide
    def chat_repo(self, db: Session) -> SQLalchemyChatRepository:
        return SQLalchemyChatRepository(db)

    @provide
    def favorite_track_repo(self, db: Session) -> SQLalchemyFavoriteTrackRepository:
        return SQLalchemyFavoriteTrackRepository(db)

    @provide
    def friendship_repo(self, db: Session) -> SQLalchemyFriendshipRepository:
        return SQLalchemyFriendshipRepository(db)

    @provide
    def member_room_association_repo(self, db: Session) -> SQLalchemyMemberRoomAssociationRepository:
        return SQLalchemyMemberRoomAssociationRepository(db)

    @provide
    def notification_repo(self, db: Session) -> SQLalchemyNotificationRepository:
        return SQLalchemyNotificationRepository(db)

    @provide
    def room_repo(self, db: Session) -> SQLalchemyRoomRepository:
        return SQLalchemyRoomRepository(db)

    @provide
    def track_repo(self, db: Session) -> SQLalchemyTrackRepository:
        return SQLalchemyTrackRepository(db)

    @provide
    def room_track_association_repo(self, db: Session) -> SQLalchemyRoomTrackAssociationRepository:
        return SQLalchemyRoomTrackAssociationRepository(db)



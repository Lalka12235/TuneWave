import uuid
from app.domain.interfaces.friendship_gateway import FriendshipGateway
from app.domain.entity import FriendshipEntity

class ReadFriendship:
    def __init__(
        self,
        friend_repo: FriendshipGateway,
    ):
        self.friend_repo = friend_repo

    def get_my_fridns(self, user_id: uuid.UUID) -> list[FriendshipEntity]:
        """
        Получает список всех принятых друзей для указанного пользователя.
        """
        friendships = self.friend_repo.get_user_friends(user_id)
        if not friendships:
            return []

        return [
            friendship for friendship in friendships
        ]

    async def get_my_sent_requests(
        self, user_id: uuid.UUID
    ) -> list[FriendshipEntity]:
        """
        Получает список всех запросов на дружбу, отправленных указанным пользователем,
        которые находятся в статусе PENDING.
        """
        requests = self.friend_repo.get_sent_requests(user_id)
        if not requests:
            return []

        return [request for request in requests]

    async def get_my_received_requests(
        self, user_id: uuid.UUID
    ) -> list[FriendshipEntity]:
        """
        Получает список всех запросов на дружбу, полученных указанным пользователем,
        которые находятся в статусе PENDING.
        """
        requests = self.friend_repo.get_received_requests(user_id)
        if not requests:
            return []

        return [request for request in requests]
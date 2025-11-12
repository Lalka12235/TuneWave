from app.models import Friendship,User
from app.repositories.friendship_repo import FriendshipRepository
from app.schemas.enum import FriendshipStatus
from datetime import datetime


def test_get_friendship_by_id(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    new_friendship: Friendship = friendship_repo.add_friend_requet(user1.id, user2.id)
    
    found_friendship: Friendship = friendship_repo.get_friendship_by_id(new_friendship.id)
    
    assert found_friendship is not None
    assert found_friendship.requester_id == user1.id
    assert found_friendship.accepter_id == user2.id
    assert found_friendship.status == FriendshipStatus.PENDING

def test_get_friendship_by_users(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    friendship_repo.add_friend_requet(user1.id, user2.id)
    
    found_friendship = friendship_repo.get_friendship_by_users(user1.id, user2.id)
    
    assert found_friendship is not None
    assert found_friendship.requester_id == user1.id
    assert found_friendship.accepter_id == user2.id

def test_get_user_friends(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    new_friendship: Friendship = friendship_repo.add_friend_requet(user1.id, user2.id)
    friendship_repo.update_friendship_status(
        new_friendship.id, 
        FriendshipStatus.ACCEPTED,
        datetime.utcnow()
    )
    
    friendships: list[Friendship] = friendship_repo.get_user_friends(user1.id)
    
    assert len(friendships) == 1
    assert friendships[0].requester_id == user1.id
    assert friendships[0].accepter_id == user2.id
    assert friendships[0].status == FriendshipStatus.ACCEPTED

def test_get_sent_requests(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    friendship_repo.add_friend_requet(user1.id, user2.id)
    
    sent_requests: list[Friendship] = friendship_repo.get_sent_requests(user1.id)
    
    assert len(sent_requests) == 1
    assert sent_requests[0].requester_id == user1.id
    assert sent_requests[0].status == FriendshipStatus.PENDING

def test_get_received_requests(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    friendship_repo.add_friend_requet(user1.id, user2.id)

    received_requests: list[Friendship] = friendship_repo.get_received_requests(user2.id)
    
    assert len(received_requests) == 1
    assert received_requests[0].accepter_id == user2.id
    assert received_requests[0].status == FriendshipStatus.PENDING

def test_add_friend_request(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    friendship: Friendship = friendship_repo.add_friend_requet(user1.id, user2.id)
    
    assert friendship is not None
    assert friendship.requester_id == user1.id
    assert friendship.accepter_id == user2.id
    assert friendship.status == FriendshipStatus.PENDING

def test_update_friendship_status(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    friendship: Friendship = friendship_repo.add_friend_requet(user1.id, user2.id)
    
    now = datetime.utcnow()
    result: bool = friendship_repo.update_friendship_status(
        friendship.id,
        FriendshipStatus.ACCEPTED,
        now
    )
    
    assert result is True

    updated_friendship: Friendship = friendship_repo.get_friendship_by_id(friendship.id)
    assert updated_friendship.status == FriendshipStatus.ACCEPTED
    assert updated_friendship.accepted_at is not None

def test_delete_friendship(create_table, friendship_repo: FriendshipRepository, user_data1: dict, user_data2: dict):
    user1 = User(**user_data1)
    user2 = User(**user_data2)
    
    friendship: Friendship = friendship_repo.add_friend_requet(user1.id, user2.id)
    
    result: bool = friendship_repo.delete_friendship(friendship.id)
    
    assert result is True
    
    found_friendship: Friendship | None = friendship_repo.get_friendship_by_id(friendship.id)
    assert found_friendship is None
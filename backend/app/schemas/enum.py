from enum import Enum

class ControlAction(Enum):
    PLAY = 'play'
    PAUSE = 'pause'
    SKIP = 'skip'


class Role(Enum):
    OWNER = 'owner'
    MODERATOR = 'moderator'
    MEMBER = 'member'
    

class FriendshipStatus(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'


class NotificationType(Enum):
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    FRIEND_DECLINED = "friend_declined"
    FRIENDSHIP_DELETED = "friendship_deleted"
    MESSAGE = "message"
    SYSTEM_MESSAGE = "system_message"
    ROOM_INVITE = "room_invite"
    ACCPET = 'accept'
    DECLINE = 'decline'
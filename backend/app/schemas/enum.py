from enum import Enum

class ControlAction(Enum):
    PLAY = 'play'
    PAUSE = 'pause'
    SKIP = 'skip'


class Role(Enum):
    OWNER = 'owner'
    MODERATOR = 'moderator'
    MEMBER = 'member'
    
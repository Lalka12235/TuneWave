class RoomNotFoundException(Exception):
    """Исключение для случая, когда комната не найдена."""
    pass

class UserNotInRoomException(Exception):
    """Исключение для случая, когда пользователь не состоит в комнате."""
    pass

class RoomFullException(Exception):
    """Исключение для случая, когда комната полна."""
    pass

class UnauthorizedRoomActionException(Exception):
    """Исключение для несанкционированных действий с комнатой."""
    pass

class RoomPasswordIncorrectException(Exception):
    """Исключение для неверного пароля комнаты."""
    pass

class TrackNotFoundException(Exception):
    """Исключение для случая, когда трек не найден в базе данных."""
    pass

class TrackAlreadyInQueueException(Exception):
    """Исключение для случая, когда трек уже находится в очереди комнаты."""
    pass
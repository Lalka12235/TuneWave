class RoomNotFoundError(Exception):
    def __init__(self, detail: str = 'Комната не найдена'):
        super().__init__(detail)

class UserNotInRoomError(Exception):
    def __init__(self, detail: str = 'Вы не находитесь в комнате'):
        super().__init__(detail)

class RoomAlreadyExistsError(Exception):
    def __init__(self, detail: str = 'Комната уже существует'):
        super().__init__(detail)
    
class PrivateRoomRequiresPasswordError(Exception):
    def __init__(self, detail: str = 'Для приватной комнаты требуется пароль.'):
        super().__init__(detail)

class PublicRoomCannotHavePasswordError(Exception):
    def __init__(self, detail: str = 'Пароль не может быть установлен для не приватной комнаты.'):
        super().__init__(detail)

class RoomPermissionDeniedError(Exception):
    def __init__(self, detail: str = 'У вас нет прав для управления комнатой'):
        super().__init__(detail)

class TrackAlreadyInQueueError(Exception):
    def __init__(self, detail: str = 'Трек уже находится в очереди'):
        super().__init__(detail)

class RoomHostNotFoundError(Exception):
    def __init__(self, detail: str = 'В комнате нет активного хоста воспроизведения. Пожалуйста, назначьте хоста'):
        super().__init__(detail)

class UserInRoomError(Exception):
    def __init__(self, detail: str = 'Вы уже являетесь участником этой комнаты.'):
        super().__init__(detail)

class InvalidRoomPasswordError(Exception):
    def __init__(self, detail: str = 'Неверный пароль для приватной комнаты.'):
        super().__init__(detail)

class SelfInteractionError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)

class RoleConflictError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)

class OwnerRoleChangeError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)

class InvalidActionError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
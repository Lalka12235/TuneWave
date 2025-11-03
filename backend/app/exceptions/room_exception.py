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
class FriendshipError(Exception):
    """Базовый класс для всех ошибок, связанных с дружбой."""
    def __init__(self, detail: str):
        super().__init__(detail=detail)

class RequesterNotFoundError(FriendshipError):
    """Ошибка: отправитель запроса дружбы не найден."""
    def __init__(self, detail: str = 'Отправитель запроса не найден'):
        super().__init__(detail=detail)

class ReceiverNotFoundError(FriendshipError):
    """Ошибка: получатель запроса дружбы не найден."""
    def __init__(self, detail: str = 'Получатель запроса не найден'):
        super().__init__(detail=detail)

class SelfFriendshipError(FriendshipError):
    """Ошибка: попытка добавить себя в друзья."""
    def __init__(self, detail: str = 'Невозможно добавить себя в друзья'):
        super().__init__(detail=detail)

class PendingRequestError(FriendshipError):
    """Ошибка: запрос на дружбу уже существует."""
    def __init__(self, detail: str = 'Запрос на дружбу уже отправлен'):
        super().__init__(detail=detail)

class ExistingFriendshipError(FriendshipError):
    """Ошибка: пользователи уже являются друзьями."""
    def __init__(self, detail: str = 'Пользователи уже являются друзьями'):
        super().__init__(detail=detail)

class FriendshipNotFoundError(FriendshipError):
    """Ошибка: запись о дружбе не найдена."""
    def __init__(self, detail: str = 'Запись о дружбе не найдена'):
        super().__init__(detail=detail)

class FriendshipPermissionError(FriendshipError):
    """Ошибка: нет прав для выполнения операции с дружбой."""
    def __init__(self, detail: str = 'Недостаточно прав для выполнения этой операции'):
        super().__init__(detail=detail)

class FriendshipStateError(FriendshipError):
    """Ошибка: некорректное состояние дружбы для выполнения операции."""
    def __init__(self, detail: str = 'Некорректное состояние записи о дружбе'):
        super().__init__(detail=detail)
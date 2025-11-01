class UserAlrediExist(Exception):
    """
    Исключение для созданного пользователя
    """
    def __init__(self, *args):
        super().__init__(*args)


class UserNotFound(Exception):
    """
    Исключение для не найденого пользователя
    """
    def __init__(self, *args):
        super().__init__(*args)

    
class ServerError(Exception):
    """
    Неизвестная ошибка на сервер
    """
    def __init__(self, *args):
        super().__init__(*args)


class UserNotPermission(Exception):
    """
    У пользователя недостаточно прав
    """
    def __init__(self, *args):
        super().__init__(*args)


class UserNotAuthorized(Exception):
    """
    Пользователь не авторизован
    """
    def __init__(self, *args):
        super().__init__(*args)


class AvatarFyleType(Exception):
    """
    Не поддерживаемый тип файла
    """
    def __init__(self, *args):
        super().__init__(*args)


class FileExceedsSize(Exception):
    """
    Файл превышает допустимый размер
    """
    def __init__(self, *args):
        super().__init__(*args)
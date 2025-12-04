class UserAlrediExist(Exception):
    """
    Исключение для созданного пользователя
    """

    def __init__(self, **kwargs):
        super().__init__(*kwargs)


class UserNotFound(Exception):
    """
    Исключение для не найденого пользователя
    """
    def __init__(self, **kwargs):
        super().__init__(*kwargs)

    
class UserNotPermission(Exception):
    """
    У пользователя недостаточно прав
    """
    def __init__(self, **kwargs):
        super().__init__(*kwargs)


class UserNotAuthorized(Exception):
    """
    Пользователь не авторизован
    """
    def __init__(self, **kwargs):
        super().__init__(*kwargs)


class AvatarFyleType(Exception):
    """
    Не поддерживаемый тип файла
    """
    def __init__(self, **kwargs):
        super().__init__(*kwargs)


class FileExceedsSize(Exception):
    """
    Файл превышает допустимый размер
    """
    def __init__(self, **kwargs):
        super().__init__(*kwargs)
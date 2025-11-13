class ServerError(Exception):
    """
    Неизвестная ошибка на сервер
    """
    def __init__(self, *args):
        super().__init__(*args)
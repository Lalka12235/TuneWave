class ServerError(Exception):
    """
    Неизвестная ошибка на сервер
    """
    def __init__(self, **kwargs):
        super().__init__(*kwargs)
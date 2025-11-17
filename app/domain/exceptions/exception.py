class ServerError(Exception):
    """
    Неизвестная ошибка на сервер
    """
    def __init__(self,detail: str, *args):
        super().__init__(*args)
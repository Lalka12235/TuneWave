class RoomNotFound(Exception):
    def __init__(self, detail: str = 'Комната не найдена'):
        super().__init__(detail)
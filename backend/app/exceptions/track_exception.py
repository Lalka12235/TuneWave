class TrackNotFound(Exception):
    def __init__(self, detail: str = 'Трек не найден'):
        super().__init__(detail)


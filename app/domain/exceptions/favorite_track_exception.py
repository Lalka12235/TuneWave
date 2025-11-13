class TrackNotFound(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)

class TrackInFavorite(Exception):
    def __init__(self, detail: str = 'Этот трек уже добавлен в ваш список любимых.'):
        super().__init__(detail)
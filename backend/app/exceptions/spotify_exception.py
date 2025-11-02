class SpotifyAPIError(Exception):
    def __init__(self, detail: str,status_code: int):
        super().__init__(detail,status_code)


class SpotifyAuthorizeError(SpotifyAPIError):
    def __init__(self, detail: str):
        super().__init__(detail)


class CommandError(SpotifyAPIError):
    def __init__(self, detail: str):
        super().__init__(detail)
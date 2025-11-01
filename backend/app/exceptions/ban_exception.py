class UserBannedInRoom(Exception):
    def __init__(self, detail: str = 'Пользователь уже забанен в этой комнате.'):
        super().__init__(detail)

class UserBannedGlobal(Exception):
    def __init__(self, detail: str = 'Пользователь уже забанен глобально.'):
        super().__init__(detail)


class UserNotExistingBan(Exception):
    def __init__(self, detail: str = 'Бан не найден или уже был снят.'):
        super().__init__(detail)
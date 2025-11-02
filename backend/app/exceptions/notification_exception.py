class NotificationNotFound(Exception):
    def __init__(self, detail: str = 'Уведомление не найдено'):
        super().__init__(detail)


class NotificationNotPermission(Exception):
    def __init__(self, detail: str = 'У вас нет прав для этого уведомления'):
        super().__init__(detail)
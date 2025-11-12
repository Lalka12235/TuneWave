from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from app.exceptions.exception import ServerError
from app.exceptions.user_exception import (
    UserAlrediExist,
)

def register_errors_handlers(app: FastAPI) -> None:

    @app.exception_handler(ServerError)
    def handler_server_error(
        request: Request,
        exc: ServerError,
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "Неизвестная ошибка на сервере. Попробуйте позже",
                "error": exc.errors(),
            }
        )
    
    @app.exception_handler(UserAlrediExist)
    def handle_user_alredi_exist(
        req: Request,
        exc: UserAlrediExist
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'message': 'Такой пользователь уже существует',
                'error': exc.errors(),
            }
        )
    
    

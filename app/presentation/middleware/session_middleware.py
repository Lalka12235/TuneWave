from app.config.log_config import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.application.services.indentity_provider import IndentityProvider

class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.identity = IndentityProvider()

    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get('session_id')
        
        self.identity.set_session_id(session_id) 

        try:
            request.state.user = self.identity.get_current_user()
        except Exception:
            request.state.user = None

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(f"{request.method} {request.url} - ERROR")
            raise e
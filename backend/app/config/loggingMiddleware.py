import logging
from fastapi import Request, Response
import time
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        method = request.method
        url = request.url

        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.exception(f"{method} {url} - ERROR - {str(e)} - {process_time:.2f}ms")
            raise

        process_time = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code
        

        logger.info(f"{method} {url} - {status_code} - {process_time:.2f}ms")
        return response  
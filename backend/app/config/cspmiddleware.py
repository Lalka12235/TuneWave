from fastapi import FastAPI, Request, Response


async def cspMiddleware(request: Request, call_next):
    response: Response = await call_next(request)

    csp_policy = (
        "default-src 'self'; "                   # Всё по умолчанию — только с текущего домена
        "script-src 'self' https://cdn.jsdelivr.net; "  # Скрипты только с этих источников
        "img-src 'self' data:; "                 # Картинки с текущего сайта и data URI
        "font-src 'self'; "                        #Шрифты с текущего сайта
    )

    response.headers['Content-Security-Policy'] = csp_policy
    return response
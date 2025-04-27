from fastapi import FastAPI, Request, Response



async def csp_middleware(request: Request, call_next):
    response = await call_next(request)
    
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "font-src 'self'; "
    )
    
    response.headers['Content-Security-Policy'] = csp_policy
    return response
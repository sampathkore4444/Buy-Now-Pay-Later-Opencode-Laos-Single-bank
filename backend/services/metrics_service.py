import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class MetricsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start
        method = request.method
        path = request.url.path
        status = response.status_code
        print(f"METRIC: {method} {path} -> {status} in {elapsed*1000:.1f}ms")
        return response

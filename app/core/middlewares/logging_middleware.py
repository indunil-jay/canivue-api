import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.middleware.logging")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        start_time = time.perf_counter()
        logger.info(
            f"--> Started {method} {path} | Request-ID: {request_id} | Client: {client_host}"
        )

        try:
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - start_time) * 1000.0

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

            logger.info(
                f"<-- Finished {method} {path} | Status: {response.status_code} "
                f"| Elapsed: {process_time_ms:.2f}ms | Request-ID: {request_id}"
            )
            return response
        except Exception:
            process_time_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception(
                f"<-- Failed {method} {path} | Elapsed: {process_time_ms:.2f}ms | Request-ID: {request_id}"
            )
            raise

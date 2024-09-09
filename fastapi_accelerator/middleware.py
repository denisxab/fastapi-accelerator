import logging
import time

from fastapi import Request

from fastapi_accelerator.appstate import DEBUG


def request_log_format(
    request: Request, status_code: int, process_time: float = None
) -> str:
    """Форматировать запрос в лог строку"""
    query = request.url.query
    return (
        '{host}:{port} - "{method} {path}{query}" - {status_code}{process_time}'.format(
            host=request.client.host,
            port=request.client.port,
            method=request.method,
            path=request.url.path,
            query=f"?{query}" if query else "",
            status_code=status_code,
            process_time=f" - [{process_time:.2f} ms]" if process_time else "",
        )
    )


async def log_request_response(request: Request, call_next):
    """Логировать время выполение API запроса

    Подключение:

    app.middleware('http')(log_request_response)
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000

    debug = DEBUG() or DEBUG(request.app)
    if debug:
        logger = logging.getLogger("uvicorn")
        logger.info(request_log_format(request, response.status_code, process_time))
    response.headers["X-Process-Time"] = f"{process_time:.2f} ms"
    return response

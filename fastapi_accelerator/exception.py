import traceback
import uuid
from typing import Any, Dict

from fastapi import HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi_accelerator.appstate import DEBUG, TIMEZONE
from fastapi_accelerator.middleware import request_log_format
from fastapi_accelerator.timezone import get_datetime_now


async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Кастомный обработки исключений

    Подключение:

        from starlette.exceptions import HTTPException as StarletteHTTPException
        app.exception_handler(StarletteHTTPException)(custom_http_exception_handler)
    """
    exc_status_code = exc.status_code
    if exc_status_code in (400, 401, 403, 404, 429, 503, 504):
        debug = DEBUG() or DEBUG(request.app)
        timezone = TIMEZONE() or TIMEZONE(request.app)

        content = {}
        content["detail"] = exc.detail
        content["context"] = request_log_format(request, exc_status_code)
        content["erorr_id"] = str(uuid.uuid4())
        content["datetime"] = get_datetime_now(timezone).isoformat()
        content["host"] = request.headers["host"]
        content["http_method"] = request.method
        content["request_path"] = request.url.path
        content["query_params"] = dict(request.query_params)
        content["user-agent"] = request.headers.get("User-Agent", "unknown")

        # Добавляем трассировку стека в debug режиме
        if debug:
            content["traceback"] = traceback.format_exc()
        return JSONResponse(
            status_code=exc_status_code, content=content, headers=exc.headers
        )
    return await http_exception_handler(request, exc)


class HTTPException404(HTTPException):
    detail = "Ресурс не найден. Пожалуйста, проверьте URL."

    def __init__(
        self,
        detail: Any = None,
        headers: Dict[str, str] | None = None,
    ) -> None:
        detail = detail or self.detail
        super().__init__(404, detail, headers)


class HTTPException403(HTTPException):
    detail = "Доступ к ресурсу запрещен."

    def __init__(
        self,
        detail: Any = None,
        headers: Dict[str, str] | None = None,
    ) -> None:
        detail = detail or self.detail
        super().__init__(403, detail, headers)


class HTTPException400(HTTPException):
    detail = "Ошибка обработки запроса."

    def __init__(
        self,
        detail: Any = None,
        headers: Dict[str, str] | None = None,
    ) -> None:
        detail = detail or self.detail
        super().__init__(400, detail, headers)

"""Модуль для работы с интеграциями внешних сервисов по протоколу HTTP."""

from enum import Enum
from functools import wraps
from typing import Awaitable, Callable, NamedTuple, TypeVar
from urllib.parse import ParseResult, urlparse

import httpx
from fastapi import HTTPException

from fastapi_accelerator.integration.base_integration import (
    URL,
    BaseIntegration,
    convert_response,
)
from fastapi_accelerator.integration.stability_patterns import StabilityError

R = TypeVar("R")  # Объявляем обобщенный тип для возвращаемого значения


class HTTPMethod(str, Enum):
    """Доступные HTTP методы"""

    get = "GET"
    post = "POST"
    put = "PUT"
    patch = "PATCH"
    delete = "DELETE"


class ApiHTTP(NamedTuple):
    """Stores API connection details and client."""

    credentials: dict | None  # Authentication credentials
    url: ParseResult  # Parsed URL of the API endpoint
    version: str  # API version
    httpmethod: str  # Use HTTP method
    client: httpx.AsyncClient | None  # HTTP client for making requests (None in tests)


class IntegrationHTTP(BaseIntegration):
    """
    Класс для интеграции с сервисами REST API.

    Этот класс используется для регистрации конечных точек в классе `EndpointsDeclaration`
    используя декоратор `@endpoint`. Это обеспечивает структурированный способ определения
    и интеграция с API.
    """

    def __init__(self, name: str, doc: str):
        # Документаци интеграции
        self._doc = doc
        # Информация о классе
        self._class_info = {
            "name": self.__class__.__name__,
            "docstring": self._doc,
            "methods": [],
        }
        # Человеоко понятное имя
        self.name = name

    def _add_integrations_method(
        self,
        func: Callable,
        path: str,
        version: str,
        docurl: str,
        httpmethod: HTTPMethod,
    ):
        """Добавьте документацию по методу интеграции."""
        # Добавить документацию функции
        self._class_info["methods"].append(
            {
                "name": func.__name__,
                "docstring": getattr(func, "__doc__", ""),
                "annotations": {
                    k: v.__name__ if hasattr(v, "__name__") else str(v)
                    for k, v in func.__annotations__.items()
                    # Исключаем аргумент api
                    if k not in ("api")
                },
                "path": path,
                "httpmethod": httpmethod,
                "version": version,
                "docurl": docurl,
            }
        )

    @property
    def docs(self) -> dict:
        """Получите документацию по этой интеграции."""
        return self._class_info

    def endpoint(
        self, httpmethod: HTTPMethod, path: str, version: str, docurl: str
    ) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
        """
        Декоратор для интеграции REST-эндпоинтов с HTTP-запросами.

        Этот декоратор применяется к методам класса, наследующего от `IntegrationHTTP`,
        и обеспечивает интеграцию с внешними REST-эндпоинтами через HTTP-запросы.

        Args:
            path (str): Путь, на который отправляется запрос.
            version (str): Версия этого эндпоинта.
            docurl (str): Ссылка на документацию эндпоинта.
            httpmethod (HTTPMethod): Какой HTTP метод испольузеится.

        Returns:
            Callable[..., Awaitable[R]]: Декорированная функция, готовая для интеграции с REST-эндпоинтом.

        Примечания:
            - Метод, к которому применяется декоратор, должен быть определен в классе, наследующем от `IntegrationHTTP`
            - Для декорируемого метода должен быть указан возвращаемый тип аннотации.
            - Обязательные аргументы должны быть указаны в декораторе.

        Raises:
            ValueError: Если для интеграционной функции не указан тип возвращаемого значения.
            TypeError: Вызыван метод не у экземпляра класса

        """

        def decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:

            # Проверить что у функции указан тип ответа
            return_type = func.__annotations__.get("return")
            if not return_type:
                raise ValueError(
                    "Return type must be specified for integration function"
                )

            # Добавить метод в хранилище
            self._add_integrations_method(func, path, version, docurl, httpmethod)

            @wraps(func)
            async def wrapper(
                self_endpoint: EndpointsDeclaration, *args, **kwargs
            ) -> R:
                if not isinstance(self_endpoint, EndpointsDeclaration):
                    raise TypeError(
                        "Method must be called on an instance, not the class itself"
                    )

                # Полный путь до endpoint
                url: ParseResult = urlparse(self_endpoint.base_url + path)
                try:

                    response = await wraper_endpoint(
                        self_endpoint,
                        func,
                        url,
                        version,
                        httpmethod,
                        *args,
                        **kwargs,
                    )
                    # Конвертировать ответ в ожидаемый тип
                    return convert_response(return_type, response)
                except StabilityError as e:
                    # Если возникло исключение в обработчиках стабльности
                    raise HTTPException(
                        status_code=getattr(e, "http_status", 500),
                        detail=f"{e.__class__.__name__}: {self.__class__.__name__}.{func.__name__}: {e.message}",
                    )

            return wrapper

        return decorator


class EndpointsDeclaration:
    """
    Базовый класс для объявления интеграций с внешними API.

    Этот класс предоставляет платформу для определения и управления интеграциями API,
    включая обработку аутентификации и настройку базового URL.
    """

    integration: IntegrationHTTP | None = None

    def __init__(self, base_url: URL = "", credentials: dict | None = None):
        """
        Аргументы:
            base_url (URL): Базовый URL для API. Это может быть доменное имя или адрес в формате host:port.
            credentials (dict | None): Доступные учетные данные для аутентификации в внешней системе.

        Примечание:
            Рекомендуется задавать base_url через переменные окружения, чтобы избежать проблем с конфигурацией
            на разных уровнях (например, на production-среде) из-за межсетевых экранов или других факторов.
        """
        self.base_url = base_url
        self.credentials = credentials

    class Schema:
        """Схема Pydantic для успешных ответов.

        Эта схема описывает структуру данных, которые ожидаются в успешных ответах от REST API.
        """

    class SchemaError:
        """Схема Pydantic для неуспешных ответов.

        Эта схема описывает структуру данных, которые могут быть возвращены
        в случае ошибки при взаимодействии с REST API.
        """


async def wraper_endpoint(
    self_endpoint: EndpointsDeclaration,
    func: Callable,
    url: ParseResult,
    version: str,
    httpmethod: HTTPMethod,
    *args,
    **kwargs,
) -> R:
    """Выполнить метод с интеграцией

    Примечание:
        Эта функция можно будет заменена во вемя тестирования,
        чтобы не делать реальные запросы.
        Для этого используйте фикстуру patch_integration
    """

    async with httpx.AsyncClient() as client:
        response = await func(
            ApiHTTP(self_endpoint.credentials, url, version, httpmethod.name, client),
            *args,
            **kwargs,
        )
    return response

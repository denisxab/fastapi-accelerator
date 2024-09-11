"""Модуль для тестирования интеграций с внешними API"""

from functools import wraps
from typing import Callable
from unittest.mock import AsyncMock, patch
from urllib.parse import ParseResult

from fastapi_accelerator.integration.http_integration import (
    ApiHTTP,
    EndpointsDeclaration,
    HTTPMethod,
)


class MockRules:
    def __init__(self, mock_rules: dict[Callable, Callable]) -> None:
        """

        Аргументы:
            mock_rules (dict[Callable, Callable]): Правила подмены методов интеграции на mock.
            Если в коде вызывается интеграция, которая не указана в mock_rules, возникает исключение.
            Это предотвращает случайные реальные запросы, если вы забыли указать mock.

        """
        self._rules = mock_rules


class _IntegrationAsyncMock:
    """Класс для управления подменой методов интеграции с использованием mock-объектов."""

    async def overwrite_wraper_endpoint(
        self,
        self_endpoint: EndpointsDeclaration,
        func: Callable,
        url: ParseResult,
        version: str,
        httpmethod: HTTPMethod,
        *args,
        **kwargs,
    ):
        """Переопределяет функцию, выполняющую метод интеграции.

        Примечание:
        - Переопределение не влияет на проверку формата ответа; он остается таким же, как у исходной функции.

        Исключение:
            NotImplementedError: возникает, если попытка выполнить метод интеграции, который не переопределен.
        """
        handel = self.mock_method.get(func.__qualname__)
        if handel:
            return await handel(
                ApiHTTP(
                    self_endpoint.credentials,
                    url,
                    version,
                    httpmethod.name,
                    client=None,
                ),
                *args,
                **kwargs,
            )
        else:
            raise NotImplementedError(
                f"Функция {func.__qualname__} не переопределена"
                + "Используйте: patch_integration.add_mock_method(Класс.Метод, overwrite_функция)"
            )

    def __init__(self, mock: AsyncMock) -> None:
        """Инициализирует IntegrationAsyncMock.

        Аргументы:
            mock (AsyncMock): Мок-объект, который будет использоваться для подмены методов интеграции.
        """
        self.mock = mock
        self.mock.side_effect = self.overwrite_wraper_endpoint
        self.mock_method: dict[str, Callable] = {}

    def overwrite_method(self, func: Callable, handel: Callable):
        """Добавляет метод для подмены.

        Аргументы:
            func (Callable): Исходная функция, которую необходимо переопределить.
            handler (Callable): Функция, которая будет использоваться вместо исходной.
        """
        self.mock_method[func.__qualname__] = handel


def patch_integration(mock_rules: MockRules):
    """Декоратор для подмены методов интеграции на mock.

    Примечание:
        Вы можете хранить mock_rules в отдельных переменных и
        переиспользовать их для разных функций/методов тестирования.
    """

    def decor(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            with patch(
                "fastapi_accelerator.integration.http_integration.wraper_endpoint"
            ) as wraper_endpoint:
                # Подмена методов интеграций на mock
                i = _IntegrationAsyncMock(wraper_endpoint)
                for real_func, mock_func in mock_rules._rules.items():
                    i.overwrite_method(real_func, mock_func)

                return func(*args, **kwargs)

        return wrap

    return decor

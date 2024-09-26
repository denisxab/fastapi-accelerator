"""Модуль для реализации паттернов стабильности и отказоустойчивости при работе с внешними системами"""

import asyncio
from datetime import timedelta
from functools import wraps
from typing import Any, Awaitable, Callable, Coroutine, TypeVar


class StabilityError(Exception):
    """Базовый класс для ошибок стабильности."""

    http_status = None

    def __init__(self, message) -> None:
        self.message = message


class StabilityTimeoutError(StabilityError):
    """Ошибка, возникающая при превышении времени ожидания."""

    # Этот статус указывает, что сервер, выступающий в роли шлюза или прокси,
    # не получил своевременный ответ от вышестоящего сервера.
    http_status = 504

    def __init__(self, message="Время ожидания истекло."):
        super().__init__(message)


class CircuitBreakerError(StabilityError):
    """Ошибка, возникающая при срабатывании предохранителя."""

    # Этот статус сигнализирует, что сервер временно не может обработать запрос
    # из-за перегрузки или проведения технических работ.
    http_status = 503

    def __init__(self, message="Circuit Breaker в состоянии OPEN."):
        super().__init__(message)


class MaxRetriesExceededError(StabilityError):
    """Ошибка, возникающая при превышении максимального числа попыток."""

    # Этот статус указывает, что клиент отправил слишком много запросов за короткий период времени.
    http_status = 429

    def __init__(self, max_attempts: int):
        message = f"Превышено максимальное число попыток: {max_attempts}."
        super().__init__(message)


class ThrottlingError(StabilityError):
    """Ошибка, возникающая при превышении лимита запросов."""

    # Этот статус указывает, что клиент отправил слишком много запросов за короткий период времени.
    http_status = 429

    def __init__(self, message="Превышен лимит запросов в секунду."):
        super().__init__(message)


R = TypeVar("R")  # Объявляем обобщенный тип для возвращаемого значения


class BaseStabilityPattern:
    """Базовый класс для реализации паттерна стабильности"""

    async def run(self, func: Callable[..., Coroutine]) -> Any: ...

    def __call__(
        self, func: Callable[..., Awaitable[R]]
    ) -> Callable[..., Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> R:
            return await self.run(lambda: func(*args, **kwargs))

        return wrapper


class sp:
    """
    Содержит в себе классы реализующие паттерны стабильности.

    Рекомендуемый порядок применения паттернов стабильности:

    Fallback должен быть самым внутренним, так как он предоставляет
    альтернативное поведение в случае сбоя основной функции.
    > Fallback(alternative_func)

    Timeout следует применять сразу после Fallback, чтобы ограничить время выполнения как
    основной функции, так и резервной.
    > Timeout(seconds=timeout_seconds)

    CircuitBreaker идет следующим, чтобы предотвратить повторные вызовы, если функция постоянно
    завершается неудачно или по таймауту.
    > CircuitBreaker(fail_threshold, reset_timeout)

    Retry следует за CircuitBreaker, чтобы попытаться выполнить
    операцию несколько раз, если CircuitBreaker позволяет это.
    > RetryPattern(max_attempts=max_attempts, delay=timedelta(seconds=delay_seconds))

    Throttling применяется в последнюю очередь, чтобы ограничить частоту
    вызовов всей обёрнутой функциональности.
    > Throttling(calls_per_second=calls_per_second)
    """

    class Fallback(BaseStabilityPattern):
        """(Резервный вариант) - Предоставляет альтернативный путь выполнения в случае сбоя основного.
        Позволяет системе деградировать контролируемо, а не падать с ошибкой."""

        def __init__(self, alternative_func: Coroutine) -> None:
            """
            alternative_func: Функция которая вызолится при возникновение исключения
            """
            self.alternative_func = alternative_func

        async def run(self, func: Callable[..., Coroutine]) -> Any:
            try:
                return await func()
            except Exception:
                return await self.alternative_func()

    class Timeout(BaseStabilityPattern):
        """(Тайм-аут) - Ограничивает время ожидания ответа от внешнего сервиса. Предотвращает блокировку ресурсов при
        зависании вызова."""

        def __init__(self, seconds: int = 10) -> None:
            """
            seconds: Через сколько секунд прервать выполнение запроса
            """
            self.seconds = seconds

        async def run(self, func: Callable[..., Coroutine]) -> Any:
            try:
                return await asyncio.wait_for(func(), timeout=self.seconds)
            except asyncio.TimeoutError:
                raise StabilityTimeoutError("Function call timed out")

    class CircuitBreaker(BaseStabilityPattern):
        """(Предохранитель) - Отслеживает количество ошибок при вызове внешнего сервиса. При превышении лимита временно
        блокирует вызов, предотвращая каскадные сбои.


        Состояния Circuit Breaker:

        -   **Close** - Идет передача запросов между сервисами и подсчет количества сбоев.
            Если число сбоев за заданный интервал времени превышает пороговое значение,
            выключатель переводится в состояние Open.

        -   **Open** - Запросы от исходного сервиса немедленно возвращаются с ошибкой.
            По истечении заданного тайм-аута выключатель переводится в состояние Half-Open.

        -   **Half-open** - Выключатель пропускает ограниченное количество запросов от исходного сервиса и
            подсчитывает число успешных запросов. Если необходимое количество достигнуто, выключатель переходит
            в состояние Closed, если нет — возвращается в статус Open.
        """

        def __init__(self, fail_threshold: int = 3, reset_timeout: float = 10):
            """
            fail_threshold: Пороговое значения числа сбоев
            reset_timeout: Период сброса подсчета количества сбоев
            """
            self.fail_threshold = fail_threshold
            self.reset_timeout = reset_timeout
            self._failures = 0
            self._last_failure_time = None
            self._state = "CLOSED"

        async def run(self, func: Callable[..., Coroutine]) -> Any:
            if self._state == "OPEN":
                if (
                    asyncio.get_event_loop().time() - self._last_failure_time
                    > self.reset_timeout
                ):
                    self._state = "HALF-OPEN"
                else:
                    raise CircuitBreakerError("Circuit is OPEN")

            try:
                result = await func()
                if self._state == "HALF-OPEN":
                    self._state = "CLOSED"
                    self._failures = 0
                return result
            except Exception as e:
                self._failures += 1
                if self._failures >= self.fail_threshold:
                    self._state = "OPEN"
                    self._last_failure_time = asyncio.get_event_loop().time()
                raise e

    class RetryPattern(BaseStabilityPattern):
        """(Паттерн повторения) - Автоматически повторяет запрос при возникновении временной ошибки."""

        def __init__(
            self, max_attempts: int = 3, delay: timedelta = timedelta(seconds=1)
        ) -> None:
            """
            max_attempts: Сколько раз попытаться повторить запрос
            delay: Задержка между попытками запросов
            """
            self.max_attempts = max_attempts
            self.delay = delay

        async def run(self, func: Callable[..., Coroutine]) -> Any:
            attempts = 0
            while attempts < self.max_attempts:
                try:
                    return await func()
                except Exception as e:
                    attempts += 1
                    if attempts == self.max_attempts:
                        raise MaxRetriesExceededError(self.max_attempts) from e
                    await asyncio.sleep(self.delay.total_seconds())

    class Throttling(BaseStabilityPattern):
        """(Регулирование) - Ограничивает количество запросов к ресурсу для предотвращения его перегрузки.
        Защищает систему от шторма запросов."""

        def __init__(self, calls_per_second: int = 1_000):
            """
            calls_per_second: Сколько разрешено запросов в секунду
            """
            self.calls_per_second = calls_per_second
            self._last_called = 0
            self._interval = 1 / calls_per_second

        async def run(self, func: Callable[..., Coroutine]) -> Any:
            current_time = asyncio.get_event_loop().time()
            time_passed = current_time - self._last_called
            # Вычисляем, сколько времени нужно подождать
            if time_passed < self._interval:
                raise ThrottlingError("Превышен лимит запросов в секунду.")
            # Обновляем время последнего вызова
            self._last_called = asyncio.get_event_loop().time()
            # Вызываем переданную функцию
            return await func()

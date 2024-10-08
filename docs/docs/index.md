# Home

![log](./images/logo.png)

## Ускоряем разработку на FastAPI: Мощный инструментарий для создания и тестирования API

В мире современной веб-разработки FastAPI зарекомендовал себя как мощный и быстрый фреймворк для создания API. Однако, при работе над крупными проектами разработчики часто сталкиваются с необходимостью оптимизировать рутинные процессы, улучшить структуру кода и упростить тестирование. В этой статье мы рассмотрим набор инструментов, который поможет решить эти задачи и существенно ускорить разработку на FastAPI.

Ходя по множеству собеседований, я заметил что многие компании, активно использующие FastAPI, разработали собственные библиотеки, но аналогичных инструментов с открытым доступом и свободной лицензией практически нет. Я, как опытный backend-разработчик на Python и Django, решил адаптировать и интегрировать наиболее полезные и востребованные решения для разработки REST API в FastAPI, основываясь на своем опыте работы с Django.

Краткосрочная цель: собрать обратную связь от сообщества о данной идее.

Долгосрочная цель: улучшить инструмент в open source, побуждая крупные компании отказаться от разработки и поддержки собственного проприетарного кода. Вместо этого мы стремимся создать экосистему, где компании не только используют общий инструментарий, но и активно участвуют в его совершенствовании, внося свой вклад в open-source проект.

-   https://github.com/denisxab/fastapi_accelerator
-   https://pypi.org/project/fastapi_accelerator

## Для кого это будет полезно?

-   Backend-разработчикам на Python, использующим или планирующим использовать FastAPI
-   Командам, работающим над средними и крупными проектами на FastAPI
-   Разработчикам, которые хотят улучшить структуру своих FastAPI-проектов и ускорить процесс разработки
-   Тем, кто ищет эффективные инструменты для тестирования FastAPI-приложений

## Зачем нужен этот инструментарий?

FastAPI Accelerator - это open-source инструментарий, созданный на основе лучших практик разработки REST API.

Основная цель представленного инструментария - ускорить и упростить разработку проектов на FastAPI.

Это достигается путем:

1. Подробной и хорошей документацией.
2. Предоставления переиспользуемого кода для типовых задач.
3. Внедрения универсального менеджера для работы с РСУБД.
4. Реализации ViewSet для быстрого создания представлений с базовой бизнес-логикой.
5. Интеграции аутентификации по JWT.
6. Упрощения написания и выполнения интеграционных тестов для API.
7. Оптимизации работы с Alembic для управления миграциями в production и test окружениях.
8. Стандартизация архитектуры для интеграций по HTTP.

Все эти компоненты взаимосвязаны и дополняют друг друга, автоматизируя рутинные задачи.

## Структура инструмента

Давайте рассмотрим основные компоненты нашего инструментария:

```bash
fastapi_accelerator/
├── db/             # Логика взаимодействия с РСУБД
├── pattern/        # Шаблоны для проектов
├── testutils/      # Утилиты для тестирования FastAPI
├── integration/    # Утилиты интеграций с внешними системами
├── commands/       # CLI команды
├── cache.py        # Реализация кеширования
├── auth_jwt.py     # Аутентификация по JWT
├── exception.py    # Обработка исключений
├── middleware.py   # Middleware компоненты
├── paginator.py    # Реализация пагинации
├── timezone.py     # Работа с временными зонами
├── viewset.py      # Реализация ViewSet
└── utils.py        # Общие утилиты
```

## Подключение к FastAPI

Файл `main.py`:

```python
from fastapi import FastAPI
from fastapi_accelerator.pattern.pattern_fastapi import base_pattern
from app.core.config import BASE_DIR_PROJECT, DEBUG, SECRET_KEY
from fastapi_accelerator.timezone import moscow_tz
from app.core.db import DatabaseManager
from app.core.security import AuthJWT

import app.api.v1.router as RouterV1

app = FastAPI()

# Паттерн для проекта
base_pattern(
    app,
    routers=(RouterV1.router,),
    timezone=moscow_tz,
    cache_status=True,
    debug=DEBUG,
    base_dir=BASE_DIR_PROJECT,
    database_manager=DatabaseManager,
    secret_key=SECRET_KEY,
)

# Подключить аутентификацию по JWT
AuthJWT.mount_auth(app)
```

## Основные компоненты

### Base Pattern

Функция `base_pattern` добавляет множество полезных функций в `app`, включая:

-   Заполнение `state` и другую информацию у `app`.
-   Разрешение `CORS`.
-   Подключение роутеров с поддержкой `ViewSet`.
-   Добавление метода `healthcheck`.
-   `Middleware` для отладки времени выполнения API-запросов.
-   Подробный вывод для `HTTP` исключений.

### DatabaseManager

`DatabaseManager` - это универсальный инструмент для работы с РСУБД, предоставляющий как синхронные, так и асинхронные(название начинается на `a`) методы. `DatabaseManager` использует патер одиночка, поэтому может быть легко подменен в тестах.

Пример использования:

```python
from app.core.config import DATABASE_URL, DEBUG, DEV_STATUS
from fastapi_accelerator.dbsession import MainDatabaseManager

DatabaseManager = MainDatabaseManager(DATABASE_URL, echo=DEBUG, DEV_STATUS=DEV_STATUS)
```

-   Общие характеристики

    -   `DEV_STATUS` - Индикатор режима разработки. При `DEV_STATUS=False` блокирует выполнение критических операций (`create_all`, `drop_all`, `clear_all`). Это мера безопасности для производственной среды.

-   Синхронные компоненты

    -   `database_url` - Адрес для подключения к синхронной базе данных.
    -   `engine` - Механизм синхронного взаимодействия с БД.
    -   `session` - Генератор синхронных сессий.
    -   `Base` - Базовый класс для моделей данных.

    -   Функциональность:

        -   `get_session` - Инжектор сессии БД.
        -   `get_session_transaction` - Инжектор сессии БД с поддержкой транзакций.
        -   `create_all` - Инициализация всех таблиц в БД.
        -   `drop_all` - Удаление всей структуры БД.
        -   `clear_all` - Очистка содержимого таблиц. Параметр `exclude_tables_name` позволяет исключить определенные таблицы из процесса очистки.

-   Асинхронные компоненты

    -   `adatabase_url` - Адрес для подключения к асинхронной БД.
    -   `aengine` - Асинхронный механизм работы с БД, включая пул соединений.
    -   `asession` - Генератор асинхронных сессий.

    -   Функциональность:

        -   `aget_session` - Асинхронный инжектор сессии БД.
        -   `aget_session_transaction` - Асинхронный инжектор сессии БД с поддержкой транзакций.

### OrmAsync

Этот класс оптимизирует асинхронное взаимодействие с БД:

-   `get` - Извлечение объекта по заданным критериям.
-   `get_list` - Получение набора объектов по запросу. (С возможностью глубокой выборки)
-   `update` - Модификация объектов согласно запросу.
-   `delete` - Удаление объектов по заданным параметрам.
-   `get_item` - Извлечение объекта по первичному ключу. (С возможностью глубокой выборки)
-   `create_item` - Создание нового объекта. (С возможностью каскадного создания)
-   `update_item` - Обновление объекта по первичному ключу. (С возможностью каскадного обновления)
-   `delete_item` - Удаление объекта по первичному ключу. (С возможностью каскадного удаления)

> Глубокая выборка/каскадные операции - это возможность работы со связанными данными.
> Активируется параметром `deep=True`
>
> Примеры:
>
> -   get_list, get_item - Возвращают объекты со всеми связанными данными, готовые для использования в Pydantic
> -   create_item - Создает записи в связанных таблицах
> -   update_item - Обновляет данные в связанных таблицах
> -   delete_item - Удаляет записи из связанных таблиц

### ViewSet

ViewSet позволяет быстро создавать CRUD-операции для моделей. Вот пример использования:

```python
from fastapi_accelerator.viewset import AppOrm, FullViewSet
from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas.timemeasurement import TaskExecution
from app.models.timemeasurement import TaskExecution as TaskExecutionDb

router = APIRouter(prefix="/api/v1")

class FileViewSet(FullViewSet):
    """
    Представление для работы с файлами
    """

    # Модель БД
    db_model = TaskExecutionDb
    # Модель Схемы
    pydantic_model = TaskExecution

    '''
    # Кеширование
    cache_class = redis_client
    cache_ttl = timedelta(minutes=10)

    # Пагинация
    paginator_class = DefaultPaginator

    # Включить поддержку вложенных схем pydantic
    # это значит что будет происходить рекурсивное
    # создание, обновление, удаление связанных записей
    deep_schema = True

    # Включить защиту через JWT
    dependencies = [Depends(jwt_auth)]

    # Вы можете также переопределять методы:

    async def db_update(
        self, item_id: str | int | UUID, item: type[BaseModel], aorm: OrmAsync
    ) -> object:
        """Переопределение метода db_update"""
        return await super().db_update(item_id, item, aorm)

    def list(self):
        """Переопределение метода list"""

        @self.router.get(f"{self.prefix}", tags=self.tags)
        async def get_list_items(
            skip: int = Query(0),
            limit: int = Query(100),
            aorm: OrmAsync = Depends(AppOrm.aget_orm),
        ) -> List[self.pydantic_model]:
            return await aorm.get_list(
                select(self.db_model).offset(skip).limit(limit),
                deep=self.deep_schema,
                db_model=self.db_model,
            )
        return get_list_items
    '''

router.views = [
    FileViewSet().as_view(router, prefix="/file"),
]
```

### Аутентификация по JWT

Для защиты API-эндпоинтов мы используем JWT-аутентификацию:

```python
from fastapi_accelerator.auth_jwt import BaseAuthJWT

class AuthJWT(BaseAuthJWT):
    async def check_auth(username: str, password: str) -> bool:
        """Проверка введенного логина и пароля."""
        return username == "admin" and password == "admin"

AuthJWT.mount_auth(app)
```

Пример защиты API метода:

```python
from fastapi_accelerator.auth_jwt import jwt_auth

@app.get("/check_protected", summary="Проверить аутентификацию по JWT")
async def protected_route(jwt: dict = Depends(jwt_auth)):
    return {"message": "This is a protected route", "user": jwt}
```

### Интеграций с внешними API

Большинство API-сервисов взаимодействуют с другими API или gRPC/RPC сервисами. Такие интеграции могут быть сложными и часто оказываются не полностью понятно разработчикам. Из-за этого они легко превращаются в легаси-код, который сложно поддерживать, а тестирование интеграций локально зачастую невозможно.

Важно, чтобы в проекте была библиотека, следящая за качеством написания интеграций и заставляющая документировать их для упрощения дальнейшей поддержки. Именно для этого я разработал специальные модули:

-   `IntegrationHTTP`: Класс для создания интеграций по REST HTTP.
-   `Stability Patterns`: Паттернов стабильности для применения к методам интеграции.
-   `py2dantic`: Утилита для перевода Python dict в Pydantic схему.
-   `docintegration`: Авто генерация документации, для используемых интеграций.

Преимущества использования этого подхода:

-   Явная спецификация форматов запроса и ответа.
-   Легкая переносимость кода между проектами — достаточно импортировать классы, основанные на `IntegrationHTTP`.
-   Консолидация логики внешних запросов в одном месте, что упрощает поддержку.
-   Возможность легко заменять реальные методы на `mock` для тестирования.
-   Легкое внедрение `Stability Patterns` для методов интеграции.

Для создания интеграции следуйте следующим шагам:

1.  Рекомендуется располагать код интеграций в директории `app/integration/ИмяПакетаИнтеграции`.
2.  Создать класса интеграций `app/integration/ИмяПакетаИнтеграции/endpoint.py`:

    ```python
    import httpx
    from pydantic import BaseModel

    from fastapi_accelerator.integration.http_integration import (
        ApiHTTP,
        EndpointsDeclaration,
        HTTPMethod,
        IntegrationHTTP,
    )
    from fastapi_accelerator.integration.stability_patterns import sp

    class ИмяIntegration(EndpointsDeclaration):

        integration = IntegrationHTTP(
            "Имя Интеграции",
            doc="Интеграция с ... API",
        )

        class Schema:
            """Схемы Pydantic для успешных ответов"""

            class Successful(BaseModel)
                body: str

        class SchemaError:
            """Схемы Pydantic для не успешных ответов"""

            class http400(BaseModel)
                error: str

        @integration.endpoint(
            HTTPMethod.post,
            "/путь",
            version="...",
            docurl="https://..."
        )
        @sp.RetryPattern()
        async def имя_метода(api: ApiHTTP, аргумент_1: str) -> Schema.Successful | SchemaError.http400:
            try:
                response: httpx.Response = await api.client.post(api.url.geturl(), json=...)
                return response.json()
            except httpx.RequestError as e:
                raise e
    ```

3.  Настроить и подключить интеграции к проекту `app/core/useintegration.py`:

    ```python
    """Интеграции используемые в проекте"""

    from app.integration.ИмяПакетаИнтеграции.endpoint import ИмяIntegration

    # Создание экземпляра интеграции
    имя_api = ИмяIntegration(
        # Начало для url пути
        base_url="https://путь...",
        # Доступы, которые можем использовать в методах интеграции
        credentials={...},
    )
    ```

4.  Пример использования класса интеграции в `FastAPI`:

    ```python
    from app.core.useintegration import имя_api
    from app.integration.ИмяПакетаИнтеграции.schema import ИмяSchema

    @router.get("/имя")
    async def имя(аргумент_1: str) -> ИмяIntegration.Schema.Successful:
        # Вызвать метод интеграции
        return await имя_api.имя_метода(аргумент_1)
    ```

## Тестирование

Одной из ключевых особенностей нашего инструментария является мощная система для написания и выполнения тестов. Она включает в себя:

1. Фикстуры для работы с тестовой базой данных и клиентом API.
2. Декораторы для аутентификации и применения фикстур.
3. Контекстный менеджер для отслеживания SQL-запросов.
4. Утилиты для проверки JSON-ответов.
5. Тестирование через классы.

Пример функции теста:

```python
from typing import Callable, NamedTuple

from fastapi.testclient import TestClient

from app.fixture.items_v1 import export_fixture_file
from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.testutils import apply_fixture_db, client_auth_jwt, track_queries, check_response_json


# Аутентифицировать тестового клиента
@client_auth_jwt(username="test")
# Создать тестовые данных из функции с фикстурами
@apply_fixture_db(export_fixture_file)
def test_имя(
    client: TestClient,               # Тестовый клиент для API запросов
    url_path_for: Callable,           # Функция для получения url по имени функции обработчика
    db_manager: MainDatabaseManager,  # Менеджер тестовой БД
    fixtures: NamedTuple,             # Хранит созданные данные из фикстур
):
    # Проверка количество выполняемых SQL команд
    with track_queries(db_manager, expected_count=3):
        # Запрос в API
        response = client.get(url_path_for("ИмяФункции"))
    # Проверка JSON API ответа
    check_response_json(
        response,
        200,
        {
            "id": fixtures.Имя.id,
        },
    )
```

Пример тест класса:

```python
from typing import Callable, NamedTuple

from fastapi.testclient import TestClient

from app.fixture.items_v1 import export_fixture_file
from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.testutils import apply_fixture_db
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt
from fastapi_accelerator.testutils.fixture_db.trace_sql import track_queries
from fastapi_accelerator.testutils.utils import BaseAuthJwtPytest, check_response_json

BASE_URL_V1 = "/api/v1/"

class TestИмя(BaseAuthJwtPytest):

    # Создать тестовые данных из функции с фикстурами
    @apply_fixture_db(export_fixture_file)
    def setUp(self, fixtures: NamedTuple):
        self.url = BASE_URL_V1 + "taskexecution"
        self.fixtures = fixtures # Хранит созданные данные из фикстур

    def test_имя(self, client: TestClient, db_manager: MainDatabaseManager):
        # Проверка количество выполняемых SQL команд
        with track_queries(db_manager, expected_count=3):
            # Запрос в API
            response = client.get(self.url)
        # Проверка JSON API ответа
        check_response_json(
            response,
            200,
            {
                "id": self.fixtures.Имя.id,
            },
        )
```

## Сравнение с существующими решениями

Хотя существует несколько проектов, предлагающих инструменты для разработки и тестирования FastAPI приложений, наше решение выделяется своей комплексностью и специализацией:

1. `FastAPI-Utils`: Предоставляет утилиты для разработки, но менее фокусирован на тестировании.
2. `FastAPI-SQLAlchemy`: Интегрирует FastAPI с SQLAlchemy, включая некоторые утилиты для тестирования.
3. `FastAPI-Toolkit`: Предлагает набор инструментов, но менее специализирован на задачах тестирования.
4. `freddie` - В архиве на GitHub, только viewset
5. `fastapi_viewsets` - Только viewset
6. `FastAPIwee` - Менее специализирован на задачах тестирования.

Наше решение отличается тем, что:

1. Более специфично для задач тестирования FastAPI приложений.
2. Предоставляет более широкий набор инструментов для различных аспектов тестирования.
3. Включает уникальные функции, такие как декоратор `@apply_fixture_db` и контекстный менеджер `track_queries`.
4. Предлагает комплексный подход, охватывающий различные аспекты разработки и тестирования FastAPI приложений.

## Заключение

Представленный инструментарий значительно упрощает и ускоряет разработку на FastAPI. Он предоставляет готовые решения для типовых задач, улучшает структуру проекта и облегчает тестирование. Использование этих инструментов позволит разработчикам сосредоточиться на бизнес-логике приложения, а не на технических деталях реализации.

Несмотря на наличие других инструментов в экосистеме FastAPI, наше решение выделяется своей полнотой и специализацией именно на задачах тестирования. Это делает его ценным дополнением к существующим ресурсам для разработчиков FastAPI.

Мы продолжаем развивать этот инструментарий и будем рады обратной связи от сообщества. Если у вас есть идеи по улучшению или вы нашли ошибку, пожалуйста, создайте issue в нашем репозитории на GitHub.

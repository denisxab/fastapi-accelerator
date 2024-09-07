# Ускоряем разработку на FastAPI: Мощный инструментарий для создания и тестирования API

В мире современной веб-разработки FastAPI зарекомендовал себя как мощный и быстрый фреймворк для создания API. Однако, при работе над крупными проектами разработчики часто сталкиваются с необходимостью оптимизировать рутинные процессы, улучшить структуру кода и упростить тестирование. В этой статье мы рассмотрим набор инструментов, который поможет решить эти задачи и существенно ускорить разработку на FastAPI.

Многие компании, активно использующие FastAPI, разработали собственные библиотеки, но аналогичных инструментов с открытым доступом и свободной лицензией практически нет. Я, как опытный backend-разработчик на Python и Django, решил адаптировать и интегрировать наиболее полезные и востребованные решения для разработки REST API в FastAPI, основываясь на своем опыте работы с Django.

Краткосрочная цель: собрать обратную связь от сообщества о данной идее.

Долгосрочная цель: улучшить инструмент в open source, чтобы крупные компании отказались от самописного кода и начали использовать общий инструментарий.

## Зачем нужен этот инструментарий?

Основная цель представленного инструментария - ускорить и упростить разработку проектов на FastAPI.

Это достигается путем:

1. Подробной и хорошей документацией.
2. Предоставления переиспользуемого кода для типовых задач.
3. Внедрения универсального менеджера для работы с РСУБД.
4. Реализации ViewSet для быстрого создания представлений с базовой бизнес-логикой.
5. Интеграции аутентификации по JWT.
6. Добавления удобной админ-панели.
7. Упрощения написания и выполнения интеграционных тестов для API.
8. Оптимизации работы с Alembic для управления миграциями в production и test окружениях.

Все эти компоненты взаимосвязаны и дополняют друг друга, автоматизируя рутинные задачи.

## Структура инструмента

Давайте рассмотрим основные компоненты нашего инструментария:

```bash
common/
├── db/             # Логика взаимодействия с РСУБД
├── pattern/        # Шаблоны для проектов
├── testutils/      # Утилиты для тестирования FastAPI
├── cache.py        # Реализация кеширования
├── auth_jwt.py     # Аутентификация по JWT
├── exception.py    # Обработка исключений
├── middleware.py   # Middleware компоненты
├── paginator.py    # Реализация пагинации
├── timezone.py     # Работа с временными зонами
├── viewset.py      # Реализация ViewSet
└── utils.py        # Общие утилиты
```

## Структуры проекта FastAPI

```bash
Проект/
│
├── app/
│   ├── __init__.py
│   ├── utils.py                # Пере используемый функционал для проекта
│   ├── core/                   # Содержит основные модули, такие как конфигурация, безопасность и общие зависимости.
│   │   ├── __init__.py
│   │   ├── settings_local.py   # Локальные значения для настроек, не должны быть в git, создавать непосредственно на сервере
│   │   ├── config.py           # Настройки проекта которые не зависят от внешних настроек
│   │   ├── security.py         # Логика безопасности проекта
│   │   ├── db.py               # Настройки и сессии базы данных.
│   │   ├── cache.py            # Настройки кеширования
│   │   └── dependencies.py
│   │
│   ├── api/                    # Содержит все API эндпоинты, разделенные по версиям.
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Содержит обработчики запросов для указанной версии api
│   │       │
│   │       ├── static/         # Содержит файлы статики, если они нужны
│   │       │   ├── js
│   │       │   ├── css
│   │       │   ├── img
│   │       │   └── html
│   │       │
│   │       ├── logic/          # Содержит бизнес логику
│   │       │   ├── __init__.py
│   │       │   ├── users.py
│   │       │   └── items.py
│   │       │
│   │       ├── schemas/        # Pydantic модели для валидации запросов и ответов.
│   │       │   ├── __init__.py
│   │       │   ├── user.py
│   │       │   └── item.py
│   │       │
│   │       ├── crud/           # Функции для работы с базой данных (Create, Read, Update, Delete).
│   │       │   ├── __init__.py
│   │       │   ├── user.py
│   │       │   └── item.py
│   │       │
│   │       └── tests/          # Директория для тестов.
│   │           ├── __init__.py
│   │           ├── test_users.py
│   │           └── test_items.py
│   │
│   ├── models/             # Определения моделей базы данных (например, SQLAlchemy модели).
│   │    ├── __init__.py
│   │    ├── user.py
│   │    └── item.py
│   │
│   └── fixture/          # Хранит фикстуры для тестирования этого проекта
│       ├── __init__.py
│       ├── items_v1.py   # Тестовые записи для БД
│       └── utils.py      # Переиспользуемые фикстуры для тестов
│
├── common/               # Submodule для переиспользовать
│
├── alembic/              # Директория для миграций базы данных.
│   ├── versions/         # Папка с миграциями
│   │   ├── __init__.py
│   │   └── 0001_init.py  # Файл с миграцией
│   └── env.py            # Настройки для alembic
│
├─ conf/                            # Файлы конфигурации для prod
│   ├── settings_local.example.py   # Пример для создания settings_local.py
│   └── Dockerfile                  # Файл для prod
│
├── pytest.ini          # Конфигурация для pytest
├── conftest.py         # Настройки выполнения тестов
│
├── .gitignore          # Какие игнорировать файлы и папки в git
├── .gitlab-ci.yml      # Настройки CI pipeline
│
├── pyproject.toml      # Настройки Poetry
│
├── Makefile            # Переиспользуемые bash команды
│
├── README.md           # Описание проекта
├── CHANGELOG.md        # Изменения в проекте
├── version.toml        # Версия проекта
│
├── alembic.ini         # Конфигурации для alembic
│
├── DockerfileDev       # Файл для создания dev контейнера с APP
├── docker-compose.yml  # Используется для сборки dev окружения
│
├── admin_panel.py      # Админ панель
│
└── main.py             # Точка входа в приложение, где создается экземпляр FastAPI.
```

## Подключение в FastAPI

Файл `main.py`:

```python
from fastapi import FastAPI
from common.pattern.pattern_fastapi import base_pattern
from app.core.config import BASE_DIR_PROJECT, DEBUG, SECRET_KEY
from common.timezone import moscow_tz
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

`DatabaseManager` - это универсальный инструмент для работы с РСУБД, предоставляющий как синхронные, так и асинхронные методы. Он использует паттерн одиночки для эффективного управления подключениями к базе данных.

Пример использования:

```python
from app.core.config import DATABASE_URL, DEBUG, DEV_STATUS
from common.dbsession import MainDatabaseManager

DatabaseManager = MainDatabaseManager(DATABASE_URL, echo=DEBUG, DEV_STATUS=DEV_STATUS)
```

### ViewSet

ViewSet позволяет быстро создавать CRUD-операции для моделей. Вот пример использования:

```python
from common.viewset import AppOrm, FullViewSet
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
                self.db_model,
                select(self.db_model).offset(skip).limit(limit),
                deep=self.deep_schema,
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
from common.auth_jwt import BaseAuthJWT

class AuthJWT(BaseAuthJWT):
    def check_auth(username: str, password: str) -> bool:
        """Проверка введенного логина и пароля."""
        return username == "admin" and password == "admin"

AuthJWT.mount_auth(app)
```

Пример защиты API метода:

```python
from common.auth_jwt import jwt_auth

@app.get("/check_protected", summary="Проверить аутентификацию по JWT")
async def protected_route(jwt: dict = Depends(jwt_auth)):
    return {"message": "This is a protected route", "user": jwt}
```

### Админ-панель

Для удобного управления данными мы интегрировали Flask-Admin:

```python
from flask import Flask

from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME, SECRET_KEY
from app.db.base import DatabaseManager
from app.models import File, User
from common.pattern_flask_admin import base_pattern

app = Flask(__name__)

admin = base_pattern(
    app,
    SECRET_KEY,
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    # > Модели которые нужны в админ панели
    models=[User, File],
    database_manager_sync=DatabaseManager,
)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8001,
        debug=True,
    )
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
from common.db.dbsession import MainDatabaseManager
from common.testutils import apply_fixture_db, client_auth_jwt, track_queries, check_response_json


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
from common.db.dbsession import MainDatabaseManager
from common.testutils import apply_fixture_db
from common.testutils.fixture_auth import client_auth_jwt
from common.testutils.fixture_db.trace_sql import track_queries
from common.testutils.utils import BaseAuthJwtPytest, check_response_json

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
4. `FastAPI-Admin`: Фокусируется на создании админ-панелей, предлагая ограниченные возможности для тестирования.

Наше решение отличается тем, что:

1. Более специфично для задач тестирования FastAPI приложений.
2. Предоставляет более широкий набор инструментов для различных аспектов тестирования.
3. Включает уникальные функции, такие как декоратор `@apply_fixture_db` и контекстный менеджер `track_queries`.
4. Предлагает комплексный подход, охватывающий различные аспекты разработки и тестирования FastAPI приложений.

## Заключение

Представленный инструментарий значительно упрощает и ускоряет разработку на FastAPI. Он предоставляет готовые решения для типовых задач, улучшает структуру проекта и облегчает тестирование. Использование этих инструментов позволит разработчикам сосредоточиться на бизнес-логике приложения, а не на технических деталях реализации.

Несмотря на наличие других инструментов в экосистеме FastAPI, наше решение выделяется своей полнотой и специализацией именно на задачах тестирования. Это делает его ценным дополнением к существующим ресурсам для разработчиков FastAPI.

Мы продолжаем развивать этот инструментарий и будем рады обратной связи от сообщества. Если у вас есть идеи по улучшению или вы нашли ошибку, пожалуйста, создайте issue в нашем репозитории на GitHub.

Мы верим, что наш инструментарий станет важным ресурсом для разработчиков FastAPI, особенно для тех, кто ищет более структурированный и комплексный подход к разработке и тестированию.

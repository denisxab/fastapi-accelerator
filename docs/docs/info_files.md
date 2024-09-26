## Описание файлов в составе fastapi_accelerator

```bash
fastapi_accelerator/
│
├── db/                         # Логика взаимодействия с РСУБД
│   ├── __init__.py
│   ├── dborm.py
│   └── dbsession.py
│
├── pattern/                    # Шаблоны для проектов
│   ├── __init__.py
│   ├── pattern_fastapi.py      # Шаблоны для создания проекта на FastAPI
│   ├── pattern_alembic.py      # Шаблоны для создания Alembic
│   └── pattern_flask_admin.py  # Шаблоны для создания проекта Flask админ панели
│
├── integration/                # Утилиты интеграций с внешними системами
│   ├── __init__.py
│   ├── base_integration.py     # Базовый класс для всех типов интеграций
│   ├── http_integration.py     # Интеграции по HTTP
│   └── stability_patterns.py   # Реализация паттернов стабильности
│
├── commands/                   # CLI команды
│   ├── __init__.py
│   └── py2dantic               # Генерация схемы pydantic из python dict
│
├── testutils                   # Утилиты для тестирования FastAPI
│   ├── __init__.py
│   ├── fixture_base.py         # Основная фикстура для тестов
│   ├── fixture_db              # Фикстуры для работы с тестовой БД
│   │   ├── __init__.py
│   │   ├── apply_fixture.py
│   │   ├── db.py
│   │   └── trace_sql.py
│   ├── fixture_auth.py         # Фикстура для аутентификации клиента по JWT
│   └── utils.py
│
├── cache.py         # Реализация кеширования
├── auth_jwt.py      # Аутентификация по JWT
├── exception.py     # Обработка исключений
├── middleware.py    # Middleware компоненты
├── paginator.py     # Реализация пагинации
├── timezone.py      # Работа с временными зонами
├── appstate.py      # Получить один раз настройки проекта во время Runtime
├── viewset.py       # Реализация ViewSet
├── utils.py         # Общие утилиты
├── README.md        # Документация
└── __init__.py
```

## Примеры файлов

### Пример `main.py`

```python
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

import app.api.v1.router as RouterV1
from app.core.config import BASE_DIR_PROJECT, DEBUG, SECRET_KEY
from app.core.db import DatabaseManager
from app.core.security import AuthJWT
from fastapi_accelerator.pattern_fastapi import base_pattern
from fastapi_accelerator.timezone import moscow_tz


@asynccontextmanager
async def lifespan(app):
    """Жизненный цикл проекта"""
    yield

app = FastAPI(
    title="File ddos API",
    # Функция lifespan
    lifespan=lifespan,
    # Зависимости, которые будут применяться ко всем маршрутам в этом маршрутизаторе.
    dependencies=None,
    # Класс ответа по умолчанию для всех маршрутов.
    default_response_class=ORJSONResponse,
)

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        reload=DEBUG,
        access_log=DEBUG,
    )
```

Запускать `python main.py`

### Пример `Makefile`

```makefile
run_test:
	pytest

run_dev_server:
	python -m main

# Создать миграцию
makemigrate:
	alembic revision --autogenerate

# Применить миграции
migrate:
	alembic upgrade head
```

### Пример `config.py`

Файл `app/core/config.py`:

```python
"""
Глобальные настройки на проект.

Может содержать дополнительно преобразование значений настроек из `.settings_local`
"""

from pathlib import Path

from .settings_local import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    CACHE_STATUS,
    DATABASE_URL,
    DEBUG,
    DEV_STATUS,
    REDIS_URL,
    SECRET_KEY,
    TEST_DATABASE_URL,
)

# Путь к приложению проекта
BASE_DIR_APP = Path(__file__).parent.parent
# Путь к корню проекта
BASE_DIR_PROJECT = BASE_DIR_APP.parent

__all__ = (
    # >>> Подключения к внешним системам:
    # Url для подключения к БД
    DATABASE_URL,
    # Url для подключения к тестовой БД
    TEST_DATABASE_URL,
    # Url для подключения к Redis
    REDIS_URL,
    # >>> Статусы:
    # Режим отладки, может быть включен на тестовом сервере
    DEBUG,
    # Режим разработки, включать только в локальной разработки
    DEV_STATUS,
    # Вкл/Выкл кеширование
    CACHE_STATUS,
    # >>> Безопасность:
    SECRET_KEY,
    # Данные для входа в Flask-Admin панель
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
)
```

Файл `app/core/settings_local.py`:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://user_app:db@postgres_db:5432/db")
TEST_DATABASE_URL = "postgres://user_app:db@postgres_db:5432/testdb"

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
SECRET_KEY = "your_secret_key_here"
DEBUG = True
DEV_STATUS = False
CACHE_STATUS = True
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"
```

### Пример файловой структуры

```bash
Проект/
│
├── app/
│   ├── __init__.py
│   ├── utils.py        # Пере используемый функционал для проекта
│   ├── core/           # Содержит основные модули, такие как конфигурация, безопасность и общие зависимости.
│   │   ├── __init__.py
│   │   ├── settings_local.py   # Локальные значения для настроек, не должны быть в git, создавать непосредственно на сервере
│   │   ├── config.py           # Настройки проекта которые не зависят от внешних настроек
│   │   ├── security.py         # Логика безопасности проекта
│   │   ├── db.py               # Настройки и сессии базы данных.
│   │   ├── cache.py            # Настройки кеширования
│   │   ├── useintegration.py   # Используемые интеграции в проекте
│   │   └── dependencies.py     # Общие зависимости для проекта
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
│   ├── models/         # Определения моделей базы данных (например, SQLAlchemy модели).
│   │    ├── __init__.py
│   │    ├── user.py
│   │    └── item.py
│   │
│   ├── integration/            # Интеграции с внешними сервисами
│   │    ├── __init__.py
│   │    └── google_translate/  # Пример пакета интеграции с Google переводчик(он может быть подключен как git submodule)
│   │        ├── __init__.py
│   │        ├── schema.py      # Сдержит схемы запросов и ответов
│   │        └── view.py        # Сдержит логику интеграций
│   │
│   └── fixture/          # Хранит фикстуры для тестирования этого проекта
│       ├── __init__.py
│       ├── items_v1.py   # Тестовые записи для БД
│       └── utils.py      # Переиспользуемые фикстуры для тестов
│
├── fastapi_accelerator/         # Submodule для переиспользовать
│
├── alembic/                # Директория для миграций базы данных.
│   ├── versions/           # Папка с миграциями
│   │   ├── __init__.py
│   │   └── 0001_init.py    # Файл с миграцией
│   └── env.py              # Настройки для alembic
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

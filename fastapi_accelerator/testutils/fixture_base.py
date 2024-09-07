"""Главный модуль для тестирования проекта"""

from typing import Self

from fastapi import FastAPI

from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.utils import SingletonMeta


class SettingTest(metaclass=SingletonMeta):
    """Настройки для тестов

    Пример `app/conftest.py`:

    ```python
    from app.core.config import TEST_DATABASE_URL
    from fastapi_accelerator.db.dbsession import MainDatabaseManager

    # Вы можете указать точный список импорта, это для простоты мы импортируем все
    from fastapi_accelerator.testutils import *  # noqa E402
    from fastapi_accelerator.testutils import SettingTest

    # Нужно создать менеджер БД до импорта APP
    # чтобы паттерн одиночка создал только тестовое instance
    # а в приложение уже взялся тестовый instance
    TestDatabaseManager = MainDatabaseManager(
        TEST_DATABASE_URL, echo=False, DEV_STATUS=True
    )

    from main import app  # noqa E402

    # Отключить кеширование во время тестов
    app.state.CACHE_STATUS = False

    SettingTest(TestDatabaseManager, app, alembic_migrate=True, keepdb=True)
    ```

    """

    def __init__(
        self,
        DatabaseManager: MainDatabaseManager,
        app: FastAPI,
        alembic_migrate: bool = False,
        keepdb: bool = True,
    ) -> Self:
        """
        alembic_migrate:
            Использовать ли для создания таблиц, миграции alembic, или сразу создавать конечный вариант таблиц
            лучше использовать alembic миграции, чтобы сразу проверять и их  вов ремя тестирования
            - Если True -> использовать alembic миграции
            - Если False -> использовать create_all()

        keepdb:
            - Если True -> не удалять тестовую БД после тестов
            - Если False -> удалить тестовую БД после тестов
        """
        self.DatabaseManager = DatabaseManager
        self.app = app
        self.alembic_migrate = alembic_migrate
        self.keepdb = keepdb

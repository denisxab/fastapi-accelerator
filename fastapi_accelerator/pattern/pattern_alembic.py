# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.

from typing import Type
from fastapi_accelerator.db.dborm import T
from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.utils import SingletonMeta
from alembic import context
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool


class AlembicEnv(metaclass=SingletonMeta):
    """Преднастоенная логика для создания и выполнения миграций чрез Alembic

    1.  Установка

    ```
    poetry add alembic
    ```

    2.  Инициализация проекта

    ```
    alembic init alembic
    ```

    3.  Изменить `alembic/env.py`

    ```python
    # Импортируем менеджера БД
    from app.core.db import DatabaseManager

    # > ! Импортировать модели которые нужно отлеживать
    from app.models import *  # noqa F401

    from fastapi_accelerator.pattern.pattern_alembic import AlembicEnv

    # Преднастоенная логика для создания и выполнения миграций чрез Alembic
    AlembicEnv(DatabaseManager).run()
    ```
    """

    def __init__(
        self, DatabaseManager: MainDatabaseManager, models: list[Type[T]] = None
    ):
        """
        models: Вы можете передать в этот аргумент список модулей которые вы импортировали в файл `env.py`
            чтобы линтер считал использованным эти переменные
        """
        self.config = context.config

        # Interpret the config file for Python logging.
        # This line sets up loggers basically.
        if self.config.config_file_name is not None:
            fileConfig(self.config.config_file_name)

        # Переопределяем URL базы данных
        self.config.set_main_option("sqlalchemy.url", DatabaseManager.database_url)

        # add your model's MetaData object here
        # for 'autogenerate' support
        # from myapp import mymodel
        # target_metadata = mymodel.Base.metadata
        self.target_metadata = DatabaseManager.Base.metadata

        # other values from the config, defined by the needs of env.py,
        # can be acquired:
        # my_important_option = config.get_main_option("my_important_option")
        # ... etc.

    def run_migrations_offline(self):
        """Run migrations in 'offline' mode.

        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well.  By skipping the Engine creation
        we don't even need a DBAPI to be available.

        Calls to context.execute() here emit the given string to the
        script output.

        """
        url = self.config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=self.target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online(self):
        """Run migrations in 'online' mode.

        In this scenario we need to create an Engine
        and associate a connection with the context.

        """
        connectable = engine_from_config(
            self.config.get_section(self.config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=self.target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()

    def run(self):
        if context.is_offline_mode():
            self.run_migrations_offline()
        else:
            self.run_migrations_online()

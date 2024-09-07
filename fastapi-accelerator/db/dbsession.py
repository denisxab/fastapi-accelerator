"""
Модуль для работы РСУБД через SqlAlchemy
"""

from typing import AsyncGenerator, Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from common.db.dborm import OrmAsync
from common.utils import SingletonMeta


class BaseDatabaseManager(metaclass=SingletonMeta):
    """Базовый класс для работы с РСУБД"""

    def __init__(
        self,
        database_url: str,
        *,
        pool_size=10,
        max_overflow=0,
        echo=True,
        DEV_STATUS: bool = False,
    ):
        self.database_url = None
        self.engine = None
        self.session = None
        self.Base = None
        self.adatabase_url = None
        self.aengine = None
        self.asession = None
        self.aBase = None
        self.DEV_STATUS = None

    def get_session() -> Generator[Session, None, None]:
        pass

    def get_session_transaction() -> Generator[Session, None, None]:
        pass

    async def aget_session() -> AsyncGenerator[AsyncSession, None]:
        pass

    async def aget_session_transaction() -> AsyncGenerator[AsyncSession, None]:
        pass

    def check_dev(self):
        """Проверять включенный режим разработки"""
        if not self.DEV_STATUS:
            raise ValueError("Такое действие можно выполнять только в DEV режиме.")

    def create_all(self):
        pass

    def drop_all(self):
        pass

    async def acreate_all(self):
        pass

    async def adrop_all(self):
        pass


class DatabaseSyncSessionMixin(BaseDatabaseManager):
    """Класс для синхронной работы с РСУБД"""

    @classmethod
    def get_session(cls) -> Generator[Session, None, None]:
        """Зависимость для получения сессии базы данных"""
        session = cls.instance.session()
        try:
            yield session
        finally:
            session.close()

    @classmethod
    def get_metadata(cls) -> MetaData:
        """Получаем обновленные метаданные"""
        metadata = MetaData()
        metadata.reflect(bind=cls.instance.engine)
        return metadata

    @classmethod
    def create_all(cls):
        """Создать все таблицы"""
        cls.instance.check_dev()
        cls.instance.Base.metadata.create_all(bind=cls.instance.engine)

    @classmethod
    def drop_all(cls):
        """Удалить все таблицы из БД"""
        cls.instance.check_dev()
        cls.instance.get_metadata().drop_all(bind=cls.instance.engine)

    @classmethod
    def clear_all(cls, exclude_tables_name: list[str] = None):
        """Отчистить данные во всех таблицах

        exclude_tables_name: Список имён таблиц которые не нужно отчистить
        """
        cls.instance.check_dev()
        with cls.instance.session() as session:
            with session.begin():
                for table in reversed(cls.instance.get_metadata().sorted_tables):
                    if table.name in exclude_tables_name:
                        continue
                    session.execute(table.delete())


class DatabaseAsyncSessionMixin(BaseDatabaseManager):
    """Класс для асинхронной работы с РСУБД используя пул соединений"""

    @classmethod
    async def aget_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """Зависимость для получения сессии базы данных

        Получить сессию:

        async for asession in aget_orm():
            yield asession
        """
        async with cls.instance.asession() as asession:
            yield asession

    @classmethod
    async def aget_orm(cls) -> AsyncGenerator[OrmAsync, None]:
        """Зависимость для получения сессии базы данных

        Получить сессию:

        async for orm in aget_orm():
            yield orm
        """
        async for asession in cls.aget_session():
            yield OrmAsync(asession)

    @classmethod
    async def aget_session_transaction(cls) -> AsyncGenerator[AsyncSession, None]:
        """Зависимость для получения сессию в транзакции

        Получить сессию:

        async for asession in aget_session_transaction():
            yield asession
        """
        async with cls.instance.asession() as asession:
            async with asession.begin():
                yield asession

    @classmethod
    async def acreate_all(cls):
        cls.instance.check_dev()
        async with cls.instance.aengine.begin() as aconn:
            # await conn.run_sync(Base.metadata.drop_all)
            await aconn.run_sync(cls.instance.aBase.metadata.create_all)


class MainDatabaseManager(DatabaseSyncSessionMixin, DatabaseAsyncSessionMixin):

    def __init__(
        self,
        database_url: str,
        *,
        pool_size=10,
        max_overflow=0,
        echo=True,
        DEV_STATUS: bool = False,
    ) -> None:
        # Для синхронной работы
        self.database_url = database_url.replace("postgres://", "postgresql://")
        self.engine = create_engine(self.database_url, echo=echo)
        self.session = sessionmaker(
            self.engine,
            autocommit=False,
            autoflush=False,
        )
        self.Base = declarative_base()

        # Для асинхронной работы
        self.adatabase_url = database_url.replace(
            "postgres://", "postgresql+asyncpg://"
        )
        # Создаем асинхронный движок SQLAlchemy с пулом соединений
        self.aengine = create_async_engine(
            self.adatabase_url,
            echo=echo,  # Выводить в консоль SQL команды
            pool_size=pool_size,  # Максимальное количество соединений в пуле
            # Максимальное количество соединений,
            # которые могут быть созданы сверх pool_size
            max_overflow=max_overflow,
        )
        # Создаем асинхронную фабрику сессий
        self.asession = async_sessionmaker(
            self.aengine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        self.aBase = declarative_base()
        # Некоторые действия разрешены только в DEV режиме
        self.DEV_STATUS = DEV_STATUS

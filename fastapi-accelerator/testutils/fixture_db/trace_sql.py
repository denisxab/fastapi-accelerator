"""Модуль для работы с трассировкой SQL команд в тестовой РСУБД"""

from contextlib import contextmanager
from typing import Generator, NamedTuple

from sqlalchemy import event

from common.db.dbsession import MainDatabaseManager


class TrackerNameTuple(NamedTuple):
    """Хранит SQL команду"""

    # Текст SQL
    statement: str
    # Параметры в SQL
    params: list | dict
    executemany: bool


class SQLQueryTracker:
    """Хранит трекер запросов в РСУБД"""

    def __init__(self):
        self.queries: list[NamedTuple] = []

    def add(self, statement: str, params: tuple, executemany: bool):
        """Добавить SQL команду в трекер"""
        self.queries.append(TrackerNameTuple(statement, params, executemany))

    @property
    def count(self) -> int:
        return len(self.queries)

    def __str__(self) -> str:
        return f"{self.queries}"


@contextmanager
def track_queries(
    db_manager: MainDatabaseManager, expected_count: int = None
) -> Generator[SQLQueryTracker, None, None]:
    """
    Перехват SQL команд, для их анализа

    expected_count: Сколько ожидается выполниться SQL команд


    Пример использования:

    def test_get_list(self, client: TestClient, db_manager: MainDatabaseManager):
        with track_queries(db_manager, expected_count=2) as tracker:
            response = client.get(self.url)

        print(tracker.queries)
    """

    tracker = SQLQueryTracker()

    def _before_cursor_execute(
        conn, cursor, statement: str, params: tuple, context, executemany: bool
    ):
        tracker.add(statement, params, executemany)

    # Отлеживаем события как в синхронном так и в асинхронном engine
    event.listen(
        db_manager.aengine.sync_engine, "before_cursor_execute", _before_cursor_execute
    )
    event.listen(db_manager.engine, "before_cursor_execute", _before_cursor_execute)
    try:
        # Трекер который можно анализировать в тестах
        yield tracker
    finally:
        # Отключить отслеживание
        event.remove(
            db_manager.aengine.sync_engine,
            "before_cursor_execute",
            _before_cursor_execute,
        )
        event.remove(db_manager.engine, "before_cursor_execute", _before_cursor_execute)

        if expected_count:
            # Проверить количество sql команд
            if tracker.count != expected_count:
                raise ValueError(
                    f"{tracker.queries}\n\n{tracker.count} != {expected_count}"
                )

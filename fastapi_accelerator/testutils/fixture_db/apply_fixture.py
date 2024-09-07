"""Модуль для работы с работы с тестовыми данными для РСУБД"""

import inspect
from functools import wraps
from typing import Callable, NamedTuple

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_accelerator.testutils.fixture_base import SettingTest


@pytest.fixture(scope="session")
def fixtures():
    """Пустая фикстура в которую будет вставлены значения из декоратора apply_fixture_db"""
    yield NotImplementedError()


def apply_fixture_db(  # noqa C901
    export_func: Callable[[], NamedTuple], flush: bool = False
):
    """Декоратор, который добавляет фикстуры в БД перед тестом и удаляет их после теста.

    :param export_func: Функция, возвращающая объекты для добавления в БД.
    :param flush: Удалить данные после выполнения теста, если установлено в True.
        Не нужно указывать если вы используете фикстуры `client`,
        так как он уже выполняет отчистку всех данных в `common_setup_table`

    Пример:

    def export_fixture_task() -> NamedTuple:
        return dict_to_namedtuple(
            file1=FileDb(
                uid=uuid.UUID("469d4176-98f3-48a2-8794-0e2472bc2b7e"),
                filename="file1.txt",
                size=100,
                format="text/plain",
                extension=".txt",
            )
        )

    @apply_fixture_db(export_fixture_task)
    def test_base(client: TestClient, fixtures: NamedTuple):
        response = client.get('url')
        assert response.status_code == 200
        assert response.json() == {"uid": fixtures.file1.uid}
    """

    def up(fixtures: NamedTuple) -> NamedTuple:
        # Накатить фикстуры
        with SettingTest.instance.DatabaseManager.session() as session:
            session: Session
            try:
                session.add_all(fixtures)
                session.commit()
                for item in fixtures:
                    session.refresh(item)
            except IntegrityError as e:
                session.rollback()
                raise e

        return fixtures

    def down(fixtures: NamedTuple):
        if flush:
            # Удалить фикстуры
            with SettingTest.instance.DatabaseManager.session() as session:
                session: Session
                try:
                    for item in fixtures:
                        session.delete(item)
                    session.commit()
                except IntegrityError as e:
                    session.rollback()
                    raise e

    def decor(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            fixtures = export_func()
            try:
                up(fixtures)
                # Если ожидается аргумент fixtures
                if "fixtures" in inspect.getfullargspec(func).args:
                    # то подменяем его
                    kwargs["fixtures"] = fixtures
                return func(*args, **kwargs)
            finally:
                down(fixtures)

        return wrap

    return decor

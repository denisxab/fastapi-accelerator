"""Модуль для работы с тестовой РСУБД"""

from typing import Any, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists

from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.testutils.fixture_base import SettingTest
from fastapi_accelerator.utils import run_async


@pytest.fixture(scope="session")
def test_app() -> Generator[FastAPI, None, None]:
    yield SettingTest.instance.app


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    yield SettingTest.instance.DatabaseManager.engine


@pytest.fixture(scope="session")
def aengine() -> Generator[AsyncEngine, None, None]:
    yield SettingTest.instance.DatabaseManager.aengine


@pytest.fixture(scope="session")
def db_manager() -> Generator[MainDatabaseManager, None, None]:
    yield SettingTest.instance.DatabaseManager


@pytest.fixture(scope="session")
def common_setup_database(engine) -> Generator[None, None, None]:
    """Создает и настраивает тестовую базу данных один раз, на протяжение всех тестов."""
    # Создать БД
    if not database_exists(engine.url):
        create_database(engine.url)

    if SettingTest.instance.alembic_migrate:
        # Использовать alembic для создания таблиц через миграции
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option(
            "sqlalchemy.url", SettingTest.instance.DatabaseManager.database_url
        )
        command.upgrade(alembic_cfg, "head")
    else:
        # Создать сразу конечный вариант таблиц
        SettingTest.instance.DatabaseManager.create_all()
    try:
        yield
    finally:
        if not SettingTest.instance.keepdb:
            # Удалить таблицы после тестов
            SettingTest.instance.DatabaseManager.drop_all()


@pytest.fixture(scope="session")
def common_client() -> Generator[TestClient, None, None]:
    """Создает тестовый клиент FastAPI."""

    with TestClient(SettingTest.instance.app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def common_clean_table(common_setup_database) -> Generator:
    """Отчистка данных в таблицах, выполняется после каждого теста."""
    try:
        yield
    finally:
        # Отчистить данные в таблицах
        SettingTest.instance.DatabaseManager.clear_all(["alembic_version"])
        # Синхронный вызов асинхронного метода dispose()
        run_async(SettingTest.instance.DatabaseManager.dispose())


@pytest.fixture(scope="function")
def client(
    common_client: TestClient, common_clean_table
) -> Generator[TestClient, Any, None]:
    """Вернуть тестовый клиент FastAPI."""
    yield common_client


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, Any, None]:
    """Получить сессию к тестовой БД"""
    for session in SettingTest.instance.DatabaseManager.get_session():
        yield session

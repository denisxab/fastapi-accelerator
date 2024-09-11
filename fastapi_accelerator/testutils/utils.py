from typing import Any, Callable, Generator, Optional

import pytest
from fastapi import Response

from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt
from fastapi_accelerator.testutils.fixture_base import SettingTest


def rm_key_from_deep_dict(data: dict | list, keys: list[str]):
    """Удалить ключи из dict или из списка словарей рекурсивно.

    data: Данные для отчистки
    keys: Ключи которые нужно удалить из данных

    Пример:

    rm_key_from_deep_dict({"date": "...", "user": "..."}, ["data"])
    >>> {"user": "..."}
    """
    if isinstance(data, dict):
        # Удаляем ключи из словаря
        for key in keys:
            data.pop(key, None)  # Используем pop с None, чтобы избежать KeyError
        # Рекурсивно обрабатываем значения в словаре
        for value in data.values():
            rm_key_from_deep_dict(value, keys)
    elif isinstance(data, list):
        # Рекурсивно обрабатываем каждый элемент списка
        for item in data:
            rm_key_from_deep_dict(item, keys)

    return data


def check_response_json(
    response: Response,
    exp_status_code: int,
    exp_json: Any,
    exclude_list: Optional[list[str]] = None,
) -> bool:
    """Проверка json API ответа

    Пример:

    def test_get_item(self, client: TestClient):
        response = client.get(self.url)
        check_response_json(response, 200, {...})
    """
    assert response.status_code == exp_status_code
    response_json = response.json()
    if exclude_list:
        rm_key_from_deep_dict(response_json, exclude_list)
    assert response_json == exp_json
    return True


@pytest.fixture(scope="function")
def url_path_for() -> Generator[Callable[[str], str], None, None]:
    """Функция чтобы получить полный URL путь по названию функции

    Пример:

    ```python
    def test_base(client: TestClient, url_path_for: Callable):
        response = client.get(url_path_for("ИмяФункции"))
    ```
    """
    yield lambda name_url: SettingTest.instance.app.url_path_for(name_url)


class BasePytest:
    """
    Базовый класс для тестов с использованием pytest.

    Данный класс предоставляет методы для настройки и очистки состояния тестов.
    Наследуйте этот класс и называйте дочерний класс в формате:

    ```python
    class TestИмяКласса(BasePytest):

        def setUp(self):
            ...

        def test_метод_1(self):
            ...
    ```
    """

    # Данные для входа тестового пользователя
    TEST_USER = {"username": "test", "password": "qwerty"}

    def setup_method(self, method=None):
        """
        Вызывается перед выполнением каждого тестового метода.

        Этот метод вызывает setUp(), который может быть переопределен в дочернем классе
        для выполнения необходимой настройки перед тестами.

        :param method: Метод, который будет выполняться (тест).
        """
        self.setUp()

    def setUp(self):
        """
        Метод для выполнения необходимой настройки перед каждым тестом.

        Этот метод может быть переопределен в дочернем классе для выполнения специфической
        настройки, необходимой для тестов.
        """

    def teardown_method(self, method=None):
        """
        Вызывается после выполнения каждого тестового метода.

        Этот метод вызывает tearDown(), который может быть переопределен в дочернем классе
        для выполнения необходимой очистки после тестов.

        :param method: Метод, который был выполнен (тест).
        """
        self.tearDown()

    def tearDown(self):
        """
        Метод для выполнения необходимой очистки после каждого теста.

        Этот метод может быть переопределен в дочернем классе для выполнения специфической
        очистки, необходимой после тестов.
        """

    @classmethod
    def setup_class(cls):
        """
        Вызывается перед выполнением всех тестовых методов в классе.

        Этот метод вызывает setUpClass(), который может быть переопределен в дочернем классе
        для выполнения необходимой настройки перед всеми тестами в классе.
        """
        cls.setUpClass()

    @classmethod
    def setUpClass(cls):
        """
        Метод для выполнения необходимой настройки перед всеми тестами в классе.

        Этот метод может быть переопределен в дочернем классе для выполнения специфической
        настройки, необходимой для всех тестов в классе.
        """

    @classmethod
    def teardown_class(cls):
        """
        Вызывается после выполнения всех тестовых методов в классе.

        Этот метод может быть переопределен в дочернем классе для выполнения необходимой
        очистки после всех тестов в классе.
        """
        cls.tearDownClass()

    @classmethod
    def tearDownClass(cls):
        """
        Метод для выполнения необходимой очистки после всех тестов в классе.

        Этот метод может быть переопределен в дочернем классе для выполнения специфической
        очистки, необходимой после всех тестов в классе.
        """


class BaseAuthJwtPytest(BasePytest):
    """
    Базовый класс для тестов с использованием pytest,
    который выполняет логику аутентификации для клиента по JWT
    """

    @pytest.fixture(autouse=True)
    def setup_method(self, client):
        @client_auth_jwt()
        def inner(self, client):
            return super().setup_method()

        return inner(self, client=client)

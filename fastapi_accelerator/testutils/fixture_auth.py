from functools import wraps

from fastapi_accelerator.auth_jwt import BaseAuthJWT
from fastapi_accelerator.testutils.fixture_base import SettingTest
from fastapi_accelerator.utils import run_async


def client_auth_jwt(username: str = None):
    """Декоратор который аутентифицирует тестового клиента по JWT.

    Использование в функции:

    @client_auth_jwt(username="test"})
    def test_get_list(client: TestClient):
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.json() == []

    Использование в классе:

    class TestTaskExecution(BasePytest):

        @client_auth_jwt() # Данные для входа возьмутся из self.TEST_USER
        def test_get_list(self, client: TestClient):
            response = client.get(self.url)
            assert response.status_code == 200
            assert response.json() == []

    """
    auth_jwt: BaseAuthJWT | None = SettingTest.instance.app.state.auth_jwt

    if not auth_jwt:
        raise ValueError("No found state - auth_jwt.")

    def decor(func):

        @wraps(func)
        def wrap(*args, **kwargs):
            # username можно передать в аргументе,
            # иначе он возьмется из self.TEST_USER класса
            # в котором обвялен тестовый метод
            current_username = username or args[0].TEST_USER["username"]
            access_token: str = auth_jwt._create_access_token(
                data={
                    "sub": current_username,
                    **run_async(auth_jwt.add_jwt_body(current_username)),
                },
            )
            kwargs["client"].headers["authorization"] = f"Bearer {access_token}"
            return func(*args, **kwargs)

        return wrap

    return decor

"""
Модуль для шаблона проекта Flask Admin
"""

from typing import Type

from flask import Flask, Response, make_response, redirect, request, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView

from fastapi_accelerator.db.dbsession import MainDatabaseManager


class AuthView:
    """Логика аутентифкации в админ панели по логину и паролю"""

    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    @classmethod
    def check_auth(cls, username: str, password: str) -> bool:
        """Проверка введенного логина и пароля."""
        return username == cls.ADMIN_USERNAME and password == cls.ADMIN_PASSWORD

    @classmethod
    def requires_auth(cls):
        """Декоратор для защиты маршрутов."""
        username = request.cookies.get("flask_admin_username")
        password = request.cookies.get("flask_admin_password")
        if not username or not password or cls.check_auth(username, password):
            return False
        return True

    def is_accessible(self):
        return self.requires_auth()

    def inaccessible_callback(self, name, **kwargs):
        # Перенаправляем на страницу логина, если доступ запрещен
        return redirect(url_for("login"))


class AuthAdminIndexView(AuthView, AdminIndexView):
    pass


class AuthModelView(AuthView, ModelView):
    pass


def add_method_auth(app: Flask):
    """Добавить метод для login и logout"""

    @app.route("/login", methods=["GET"])
    def login():
        """API метод для логина."""
        auth = request.authorization
        if auth:
            resp = make_response("Setting a cookie")
            resp.set_cookie("flask_admin_username", auth.username)
            resp.set_cookie("flask_admin_password", auth.password)
            return resp
        # Ответ на неправильные данные аутентификации.
        return Response(
            "Could not verify",
            401,
            {"WWW-Authenticate": 'Basic realm="Login required!"'},
        )

    @app.route("/logout", methods=["GET"])
    def logout():
        """API метод для логаута."""
        resp = make_response("Logged out")
        resp.delete_cookie("flask_admin_username")
        resp.delete_cookie("flask_admin_password")
        return resp

    return login, logout


def base_pattern(
    app: Flask,
    SECRET_KEY: str,
    ADMIN_USERNAME: str,
    ADMIN_PASSWORD: str,
    models: list[Type],
    database_manager: MainDatabaseManager,
) -> Admin:
    """Создать Flask APP


    Пример:

    ```python
    from flask import Flask

    from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME, SECRET_KEY
    from app.core.db import DatabaseManager
    from app.models import File, User
    from fastapi_accelerator.pattern.pattern_flask_admin import base_pattern

    app = Flask(__name__)

    admin = base_pattern(
        app,
        SECRET_KEY,
        ADMIN_PASSWORD,
        ADMIN_USERNAME,
        models=[User, File],
        database_manager=DatabaseManager,
    )


    if __name__ == "__main__":
        app.run(
            host="0.0.0.0",
            port=8001,
            debug=True,
        )
    ```
    """

    app.secret_key = SECRET_KEY
    # Данные для аутентификации (логин и пароль)
    AuthView.ADMIN_USERNAME = ADMIN_USERNAME
    AuthView.ADMIN_PASSWORD = ADMIN_PASSWORD

    # Добавить метод для login и logout
    add_method_auth(app)

    admin = Admin(
        app,
        name="Админ панель",
        template_mode="bootstrap3",
        index_view=AuthAdminIndexView(),
    )

    # Подключение моделей к админ панели
    for model in models:
        admin.add_view(AuthModelView(model, database_manager.session()))
    return admin

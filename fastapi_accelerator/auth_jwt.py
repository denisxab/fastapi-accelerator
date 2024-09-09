"""Модуль для аутентификации по JWT"""

import abc
from datetime import datetime, timedelta
from typing import Annotated, Optional, Union

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from fastapi_accelerator.appstate import AUTH_JWT

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class BaseAuthJWT:
    '''
    Пример:

        class AuthJWT(BaseAuthJWT):
            def check_auth(username: str, password: str) -> bool:
                """Проверка введенного логина и пароля."""
                return username == "admin" and password == "admin"

            def add_jwt_body(username: str) -> dict:
                """Функция для добавление дополнительных данных в JWT токен пользователя"""
                return {"version": username.title()}


        # Подключить аутентификацию по JWT
        AuthJWT.mount_auth(app)

    Пример защиты API метода:

        @app.get("/cheack_protected", summary="Проверить аутентификацию по JWT")
        async def protected_route(jwt: dict = Depends(jwt_auth)):
            return {"message": "This is a protected route", "user": jwt}
    '''

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    # Установиться автоматически в mount_auth
    secret_key = None

    @abc.abstractmethod
    def check_auth(username: str, password: str) -> bool:
        """Проверка введенного логина и пароля."""
        raise NotImplementedError()

    @abc.abstractmethod
    def add_jwt_body(username: str) -> dict:
        """Функция для добавление дополнительных данных в JWT токен пользователя"""

    @classmethod
    def mount_auth(cls, app: FastAPI):
        """Подключение аутентификации по JWT"""
        # Установить класс для аутентификации
        app.state.auth_jwt = cls
        cls.secret_key = app.state.SECRET_KEY

        @app.post("/token", summary="Аутентификация по JWT", tags=["common"])
        async def login(
            user: Annotated[OAuth2PasswordRequestForm, Depends()],
        ) -> Token:
            if cls.check_auth(user.username, user.password):
                return Token(
                    access_token=cls._create_access_token(
                        data={
                            "sub": user.username,
                            **cls.add_jwt_body(user.username),
                        },
                    ),
                    token_type="bearer",
                )
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")

        @app.get(
            "/check_protected",
            summary="Проверить аутентификацию по JWT",
            tags=["common"],
        )
        async def protected_route(request: Request, jwt: dict = Depends(jwt_auth)):
            return {"message": "This is a protected route", "user": jwt}

        return login, protected_route

    @classmethod
    def _create_access_token(
        cls,
        data: dict,
        expires_delta: Union[timedelta, None] = None,
    ) -> str:
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.secret_key, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def _verify_token(cls, token: str) -> Optional[dict]:
        """Проверка валидности JWT токена"""
        try:
            payload = jwt.decode(token, cls.secret_key, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


def jwt_auth(request: Request, token: str = Depends(oauth2_scheme)) -> dict:
    """Depends для проверки JWT"""
    auth_jwt: BaseAuthJWT = AUTH_JWT() or AUTH_JWT(request.app)
    payload = auth_jwt._verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

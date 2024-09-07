"""
Модуль для высокоуровневой работы с API обработками
используя подход ViewSet которые автоматизируют базовый CRUD функционал,
и поваляют гибко переопределять логику ViewSet
"""

import abc
from datetime import timedelta
from typing import Callable, List, Optional, Type, Union
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import class_mapper

from common.cache import BaseCache, cache_redis
from common.db import MainDatabaseManager, OrmAsync
from common.db.dborm import SQL_TO_PYTHON_TYPE, T, deep_instance, get_pk
from common.exception import HTTPException404
from common.paginator import BasePaginatorClass


class BaseViewSet(abc.ABC):
    def _register_endpoint(self):
        """Регистраций API обработчиков"""


class AppOrm:
    """Брать методы получения сесси из настроек APP DATABASE_MANAGER"""

    database_manager: MainDatabaseManager = None

    @classmethod
    async def aget_orm(cls, request: Request):
        """Метод получения сессии берем из настоек APP"""
        if not cls.database_manager:
            cls.database_manager = request.app.state.DATABASE_MANAGER
        async for orm in cls.database_manager.aget_orm():
            yield orm


class ViewSetRetrieve(BaseViewSet):

    def _register_endpoint(self):
        self.retrieve()

    def retrieve(self):
        @self.router.get(
            f"{self.prefix}/{{item_id}}",
            tags=self.tags,
            dependencies=self.dependencies,
        )
        @cache_redis(self.cache_class, self.cache_ttl, self.cache)
        async def get_item(
            request: Request,
            item_id: self.type_item_id = Path(...),
            aorm: OrmAsync = Depends(AppOrm.aget_orm),
        ) -> self.pydantic_model:
            obj = await aorm.get_item(self.db_model, item_id, deep=self.deep_schema)
            if not obj:
                raise HTTPException404()
            return obj

        return get_item


class ViewSetList(BaseViewSet):
    def _register_endpoint(self):
        self.list_paginator() if self.paginator_class else self.list()

    @staticmethod
    def get_offset(page: int, size: int) -> int:
        return (page - 1) * size

    def list_paginator(self):
        """Обработчик API с пагинацией"""

        @self.router.get(
            f"{self.prefix}", tags=self.tags, dependencies=self.dependencies
        )
        @cache_redis(self.cache_class, self.cache_ttl, self.cache)
        async def get_list_items_paginator(
            request: Request,
            page: int = Query(1, gt=0),
            size: int = Query(10, gt=0),
            aorm: OrmAsync = Depends(AppOrm.aget_orm),
        ) -> self.paginator_class.Schema:
            offset = self.get_offset(page, size)
            response = await aorm.get_list(
                self.db_model,
                select(self.db_model).order_by(self.name_pk).offset(offset).limit(size),
                deep=self.deep_schema,
            )
            return self.paginator_class.json(page, size, response)

        return get_list_items_paginator

    def list(self):
        """Обработчик API"""

        @self.router.get(
            f"{self.prefix}", tags=self.tags, dependencies=self.dependencies
        )
        @cache_redis(self.cache_class, self.cache_ttl, self.cache)
        async def get_list_items(
            request: Request,
            skip: int = Query(0, gte=0),
            limit: int = Query(100, gt=0),
            aorm: OrmAsync = Depends(AppOrm.aget_orm),
        ) -> List[self.pydantic_model]:
            return await aorm.get_list(
                select(self.db_model).offset(skip).limit(limit), deep=self.deep_schema
            )

        return get_list_items


class ViewSetCreate(BaseViewSet):
    def _register_endpoint(self):
        self.create()

    def _to_db_item(self, item: Type[BaseModel]) -> T:
        """Преобразовать элемент pydantic в db_item"""
        db_item = (
            deep_instance(self.db_model, item)
            if self.deep_schema
            else self.db_model(**item.dict())
        )
        return db_item

    def create(self):
        """API обработки"""

        @self.router.post(
            f"{self.prefix}", tags=self.tags, dependencies=self.dependencies
        )
        async def create_item(
            item: self.pydantic_model, aorm: OrmAsync = Depends(AppOrm.aget_orm)
        ) -> self.pydantic_model:
            return await self.db_create(item, aorm)

        return create_item

    async def db_create(self, item: Type[BaseModel], aorm: OrmAsync) -> object:
        """Функция для создание записи в БД."""
        return await aorm.create_item(self._to_db_item(item), deep=self.deep_schema)


class ViewSetUpdate(BaseViewSet):
    def _register_endpoint(self):
        self.update()

    def update(self):
        """API обработки"""

        @self.router.put(
            f"{self.prefix}/{{item_id}}", tags=self.tags, dependencies=self.dependencies
        )
        async def update_item(
            item_id: self.type_item_id,
            item: self.pydantic_model,
            aorm: OrmAsync = Depends(AppOrm.aget_orm),
        ) -> self.pydantic_model:
            return await self.db_update(item_id, item, aorm)

        return update_item

    async def db_update(
        self, item_id: Union[str, int, UUID], item: Type[BaseModel], aorm: OrmAsync
    ) -> object:
        """Функция для обновление записи в БД"""
        return await aorm.update_item(
            self.db_model, item_id, item.dict(exclude_unset=True), deep=self.deep_schema
        )


class ViewSetDelete(BaseViewSet):
    def _register_endpoint(self):
        self.delete()

    def delete(self):
        """API обработки"""

        @self.router.delete(
            f"{self.prefix}/{{item_id}}", tags=self.tags, dependencies=self.dependencies
        )
        async def delete_item(
            item_id: self.type_item_id, aorm: OrmAsync = Depends(AppOrm.aget_orm)
        ):
            return await self.db_delete(item_id, aorm)

        return delete_item

    async def db_delete(self, item_id: Union[str, int, UUID], aorm: OrmAsync):
        """Функция для удаления записи в БД"""
        return await aorm.delete_item(self.db_model, item_id, deep=self.deep_schema)


class GenericViewSet:
    """
    from app.api.v1.schemas.file import File
    from app.models.file import File as FileDb

    router = APIRouter()

    class FileViewSet(FullViewSet):
        db_model = FileDb
        pydantic_model = File

    router.views = [
        FileViewSet().as_view(router, prefix="/file"),
    ]
    """

    # Модель БД SqlAlchemy
    db_model: Type
    # Модель Схемы
    pydantic_model: Type[BaseModel]

    # Теги для URL
    tags: Optional[List[str]]

    # Пагинация для List
    paginator_class: Optional[BasePaginatorClass]

    # Класс для кешировать ответ List, Retrieve
    cache_class: Optional[BaseCache]
    # Время жизни ответа в кеше
    cache_ttl: Optional[timedelta]

    # Включить поддержку вложенных схем pydantic
    # это значит что будет происходить рекурсивное создание, обновление, удаление связанных записей
    deep_schema: Optional[bool]

    # Зависимости на весь ViewSet
    # Например можно указать аутентификацию по JWT `[Depends(jwt_auth)]`
    dependencies: Optional[list[Callable]]

    # Какой тип у первичного ключа для Api метода
    type_item_id: Optional[type]

    def as_view(self, router: APIRouter, prefix: str):
        self._mro_class = self.__class__.mro()
        # Модель БД SqlAlchemy
        self.router: APIRouter = router
        # Модель Схемы
        self.db_model: Type = self.db_model
        self.pydantic_model: Type[BaseModel] = self.pydantic_model
        # Префикс для URL
        self.prefix: str = prefix
        # Теги
        self.tags: List[str] = getattr(self, "tags", [self._mro_class[0].__name__])
        # Имя столбца с первичным ключом
        self.name_pk: str = get_pk(self.db_model)
        # Включить поддержку вложенных схем
        self.deep_schema = getattr(self, "deep_schema", False)
        # Зависимости на весь ViewSet
        self.dependencies = getattr(self, "dependencies", [])
        # Пагинация для List
        self.paginator_class = getattr(self, "paginator_class", None)
        # Какой тип у первичного ключа для Api метода
        self.type_item_id = getattr(
            self,
            "type_item_id",
            # Попытаться определить тип автоматически по типу первичного ключа в модели
            SQL_TO_PYTHON_TYPE.get(
                class_mapper(self.db_model).primary_key[0].type.__class__,
                Union[str, int, UUID],
            ),
        )

        # Логика кеширования
        self.cache = False
        if cache_class := getattr(self, "cache_class", False):
            self.cache = True
            self.cache_class = cache_class
            self.cache_ttl = getattr(self, "cache_ttl", timedelta(seconds=3))
        else:
            self.cache_class = None
            self.cache_ttl = None

        # Подключить API обработчики
        for cls in self._mro_class:
            if cls in (
                ViewSetList,
                ViewSetCreate,
                ViewSetRetrieve,
                ViewSetUpdate,
                ViewSetDelete,
            ):
                cls._register_endpoint(self)

        # Документирование тегов
        self.openapi_tag = {"name": self.tags[0], "description": str(self)}
        return self

    def __str__(self) -> str:
        """Сформировать документацию для ViewSet"""
        description = "ViewSet"
        if doc := self._mro_class[0].__doc__:
            description = "{doc}: {db_model}{dependencies}{cache}{deep_schema}".format(
                doc=doc.strip(),
                db_model=f" **db_model**={self.db_model.__name__}",
                dependencies=(
                    f" **dependencies**=[{', '.join(d.dependency.__name__ for d in self.dependencies)}]"
                    if self.dependencies
                    else ""
                ),
                cache=(" **cache**=On" if self.cache else ""),
                deep_schema=(" **deep_schema**=On" if self.deep_schema else ""),
            )
        return description


class FullViewSet(
    ViewSetList,
    ViewSetCreate,
    ViewSetRetrieve,
    ViewSetUpdate,
    ViewSetDelete,
    GenericViewSet,
):
    pass

"""
Модуль для работы с ORM SqlAlchemy
"""

import uuid
from typing import Any, Final, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import (
    UUID,
    Boolean,
    Delete,
    Float,
    Integer,
    Select,
    String,
    Update,
    delete,
    select,
    update,
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import class_mapper, joinedload, selectinload

T = TypeVar("T", bound=DeclarativeMeta)

SQL_TO_PYTHON_TYPE: Final[dict] = {
    Integer: int,
    String: str,
    Float: float,
    Boolean: bool,
    UUID: uuid.UUID,
}


def deep_instance(db_model: Type[T], pydantic_data: BaseModel) -> T:
    """
    Создает экземпляр SQLAlchemy модели из словаря.
    Если словарь содержит вложенные данные для связанных объектов, они также будут созданы.
    """
    kwargs = {}
    for field, value in pydantic_data:
        # Если значение также является словарем, создаем вложенный объект
        if isinstance(value, BaseModel):
            # Получаем тип модели для связанного объекта
            related_model = getattr(db_model, field).property.mapper.class_
            value = deep_instance(related_model, value)
        kwargs[field] = value
    return db_model(**kwargs)


def get_pk(db_model: Type[T]) -> Any:
    """Получить первичный ключ у модели"""
    return getattr(db_model, db_model.__table__.primary_key.columns.values()[0].name)


class BaseOrm:

    def __init__(self, asession: AsyncSession):
        self.asession = asession

    async def get(self, query: Select) -> Optional[T]:
        """Получить объект по запросу"""
        response = await self.asession.execute(query)
        return response.scalar_one_or_none()

    async def get_list(
        self, db_model: Type[T], query: Select, deep: bool = False
    ) -> list[T]:
        """Получить список объектов по запросу"""
        if not deep:
            response = await self.asession.execute(query)
            return response.scalars().all()
        else:
            """Получить вложенный список объектов по запросу"""
            relationships = class_mapper(db_model).relationships
            options = [joinedload(getattr(db_model, rel.key)) for rel in relationships]
            response = await self.asession.execute(query.options(*options))
            return response.scalars().all()

    async def update(self, query: Update, update_data: dict) -> T:
        """Обновить объекты по запросу"""
        query = query.values(**update_data).returning(query.table)
        result = await self.asession.execute(query)
        await self.asession.commit()
        return result.scalars().first()

    async def delete(self, query: Delete) -> bool:
        """Удалить объекты по запросу"""
        result = await self.asession.execute(query)
        await self.asession.commit()
        return result.rowcount > 0


class OrmAsyncItem(BaseOrm):
    """Логика для работы с одним элементом"""

    async def get_item(
        self, db_model: Type[T], item_id: Union[str, int, uuid.UUID], deep: bool = False
    ) -> Optional[T]:
        """Получить объект по PK"""
        if not deep:
            # Получить имя первичного ключа
            name_pk: str = get_pk(db_model)
            return await self.get(select(db_model).filter(name_pk == item_id))
        else:
            """Получить вложенный объект"""
            return await self.asession.get(
                db_model, item_id, options=[selectinload("*")]
            )

    async def create_item(self, obj: T, deep: bool = False) -> T:
        """Создать объект"""
        if not deep:
            self.asession.add(obj)
            await self.asession.commit()
            await self.asession.refresh(obj)
            return obj
        else:
            """Создать вложенный объект"""
            self.asession.add(obj)
            await self.asession.commit()
            return await self.eager_refresh(obj)

    async def update_item(
        self,
        db_model: Type[T],
        item_id: Union[str, int, uuid.UUID],
        update_item: dict,
        deep: bool = False,
    ) -> T:
        """Обновить объект по PK"""

        if not deep:
            # Получить имя первичного ключа
            name_pk: str = get_pk(db_model)
            return await self.update(
                update(db_model).filter(name_pk == item_id), update_item
            )
        else:
            """Обновить вложенный объект"""

            async def update_nested(obj: T, update_item: dict) -> T:
                """Функция рекурсивного обновления"""
                db_model = obj.__class__
                mapper = class_mapper(db_model)
                # Связи объекта с другими таблицами
                relationships_keys = {
                    r.local_remote_pairs[0][0].key: r.key for r in mapper.relationships
                }
                # Получить имя первичного ключа
                name_pk: str = get_pk(db_model)
                # Исключаем колонки с первичными ключами
                columns = [c.key for c in mapper.column_attrs if c.key != name_pk.name]
                for column_name in columns:
                    # Взять значение входного
                    update_value = update_item.get(column_name)
                    # Если это связь с другой таблицей
                    if overwrite_column_name := relationships_keys.get(column_name):
                        related_obj = getattr(obj, overwrite_column_name)
                        nested_obj = await update_nested(
                            related_obj, update_item.get(overwrite_column_name)
                        )
                        update_value = nested_obj
                        column_name = overwrite_column_name

                    setattr(obj, column_name, update_value)
                return obj

            # Получить объект
            obj = await self.asession.get(
                db_model, item_id, options=[selectinload("*")]
            )
            if not obj:
                return NoResultFound()  # Если объект не найден, возвращаем ошибку

            # Обновить объект
            update_obj = await update_nested(obj, update_item)
            # Применить обновление в БД
            self.asession.add(update_obj)
            await self.asession.commit()
            return update_obj

    async def delete_item(
        self, db_model: Type[T], item_id: Union[str, int, uuid.UUID], deep: bool = False
    ) -> bool:
        """Удалить объект по PK"""
        if not deep:
            # Получить имя первичного ключа
            name_pk: str = get_pk(db_model)
            return await self.delete(delete(db_model).filter(name_pk == item_id))
        else:
            """Удалить вложенный объект и его зависимости."""

            # Получаем объект с его зависимостями через selectinload
            obj = await self.asession.get(
                db_model, item_id, options=[selectinload("*")]
            )
            if not obj:
                return False  # Если объект не найден, возвращаем False

            async def delete_nested(
                tmp_obj: T,
                pre_model: Optional[Type[T]] = None,
            ):
                """Рекурсивное удаление всех зависимостей объекта."""
                mapper = class_mapper(tmp_obj.__class__)

                # Находим все связи объекта с другими таблицами
                for relationship in mapper.relationships:
                    # Не пытаемся удалить запись из предыдущей итерации стека
                    if (
                        pre_model
                        and relationship.target.name == pre_model.__table__.name
                    ):
                        continue
                    related_objs = getattr(tmp_obj, relationship.key)
                    if related_objs:
                        if relationship.uselist:
                            # Если это список объектов, удаляем их рекурсивно
                            for related_obj in related_objs:
                                await delete_nested(
                                    related_obj, pre_model=tmp_obj.__class__
                                )
                        else:
                            # Если это один объект, удаляем его рекурсивно
                            await delete_nested(
                                related_objs, pre_model=tmp_obj.__class__
                            )

                # Удаляем сам объект
                await self.asession.delete(tmp_obj)

            # Начинаем рекурсивное удаление с корневого объекта
            await delete_nested(obj)
            # Коммит транзакции
            await self.asession.commit()
            return True

    async def eager_refresh(self, obj: Type[T]) -> Type[T]:
        """Жадно загрузить все связанные записи для данного объекта."""
        return await self.asession.get(
            type(obj), get_pk(obj), options=[selectinload("*")]
        )


class OrmAsync(OrmAsyncItem):
    """Взаимодействие с БД"""

    ...

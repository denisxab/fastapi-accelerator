"""
Модуль дял пагиации овтета
"""

import abc
from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel


class BasePaginatorClass(abc.ABC):
    class Schema(BaseModel):
        page: int
        size: int
        count: int
        items: dict | list

    @staticmethod
    def json(page: int, size: int, response: Any) -> dict:
        pass


class DefaultPaginator(BasePaginatorClass):
    class Schema(BaseModel):
        page: int
        size: int
        count: int
        items: dict | list

    @staticmethod
    def json(page: int, size: int, response: Any) -> dict:
        items = jsonable_encoder(response)
        return {
            "page": page,
            "size": size,
            "count": len(items),
            "items": items,
        }

"""
Работа с кеш Redis
"""

import json
from datetime import timedelta
from functools import wraps
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from redis import Redis

from fastapi_accelerator.appstate import CACHE_STATUS


class BaseCache:

    async def get(key: str) -> Any: ...
    async def set(key: str, data: str, ex: timedelta = None): ...


class BaseRedis(BaseCache, Redis):
    pass


def cache_redis(cache_class: BaseCache, cache_ttl: timedelta, cache: bool = True):
    """
    Декоратор для кеширования ответов API в Redis.

    Args:
        cache_class: Класс кеша для взаимодействия с Redis.
        cache_ttl: Время жизни кеша.
        cache: Флаг, включающий или отключающий кеширование.

    Returns:
        Callable: Декоратор функции.

    class ViewSetRetrieve(BaseViewSet):
        def register_routes(self):
            '''Регистраций API обработчиков'''

            @self.router.get(f"{self.prefix}/{{item_uid}}", tags=self.tags)
            @cache_redis(self.cache, self.cache_class, self.cache_ttl)
            async def get_item(
                request: Request,
                item_uid: str = Path(...),
                aorm: OrmAsync = Depends(AppOrm.aget_orm),
            ) -> self.pydantic_model:
                response = await aorm.get(
                    select(self.db_model).filter(self._name_pk == item_uid)
                )
                return response

            return get_item
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs["request"]

            cache_status = CACHE_STATUS() or CACHE_STATUS(request.app)

            if not cache_status or not cache:
                # кеш отключен
                return await func(*args, **kwargs)

            key_cache: str = f"{request.url.path}?{request.url.query}"
            cache_response = await cache_class.get(key_cache)
            if cache_response:
                # Создаем ответ с заголовком, указывающим, что данные из кеша
                return JSONResponse(
                    content=json.loads(cache_response), headers={"X-Cache": "HIT"}
                )

            response = await func(*args, **kwargs)

            json_data = jsonable_encoder(response)
            await cache_class.set(key_cache, json.dumps(json_data), ex=cache_ttl)
            # Возвращаем результат с заголовком
            return JSONResponse(content=json_data, headers={"X-Cache": "MISS"})

        return wrapper

    return decorator

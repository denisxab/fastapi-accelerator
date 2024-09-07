"""
Работа с кеш Redis
"""

from datetime import timedelta
import json
from functools import wraps
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from redis import Redis


class BaseCache:

    async def get(key: str) -> Any: ...
    async def set(key: str, data: str, ex: timedelta = None): ...


class BaseRedis(BaseCache, Redis):
    pass


def cache_redis(cache_class: BaseCache, cache_ttl: timedelta, cache: bool = True):
    """
    Пример использования:

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
    # Глобальный статус кеширования
    CACHE_STATUS = None

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal CACHE_STATUS
            request: Request = kwargs["request"]

            if CACHE_STATUS is None:
                CACHE_STATUS = request.app.state.CACHE_STATUS
            if not CACHE_STATUS:
                # кеш отключен
                return await func(*args, **kwargs)

            key_cache: str = f"{request.url.path}?{request.url.query}"
            if cache:
                cache_response = await cache_class.get(key_cache)
                if cache_response:
                    # Создаем ответ с заголовком, указывающим, что данные из кеша
                    return JSONResponse(
                        content=json.loads(cache_response), headers={"X-Cache": "HIT"}
                    )

            response = await func(*args, **kwargs)

            if cache:
                json_data = jsonable_encoder(response)
                await cache_class.set(key_cache, json.dumps(json_data), ex=cache_ttl)
                # Возвращаем результат с заголовком
                return JSONResponse(content=json_data, headers={"X-Cache": "MISS"})
            return response

        return wrapper

    return decorator

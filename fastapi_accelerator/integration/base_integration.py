"""Модуль для работы с интеграциями внешних сервисов"""

from types import GenericAlias, UnionType
from typing import Any, List, NewType, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic_core import ValidationError

URL = NewType("URL", str)


class BaseIntegration:
    """Базовый класс для интеграций"""

    ...


def convert_response(
    rtypes: GenericAlias, data: Union[Any, dict, list]
) -> Union[Any, BaseModel, List[BaseModel]]:
    """
    Конвертирует входные данные в модель Pydantic или список моделей.

    Эта функция пытается преобразовать входные данные в указанный тип или типы.
    Она поддерживает одиночные типы, Union типы, и списки типов.

    Args:
        rtypes (GenericAlias):
            Ожидаемый тип или типы ответа. Может быть одиночным типом или Union из нескольких типов.
        data (Union[dict, list]):
            Данные для конвертации. Могут быть словарем или списком.

    Returns:
        Union[dict, list, BaseModel, List[BaseModel]]: Сконвертированные данные.
        Если конвертация не удалась или не требовалась, возвращаются исходные данные.

    Raises:
        ValidationError: Если все попытки конвертации завершились неудачно.
    """
    # Если rtypes - это Union, разворачиваем его в список типов.
    # В противном случае, создаем список из одного элемента.
    rtypes = rtypes.__args__ if isinstance(rtypes, UnionType) else [rtypes]

    # Определяем, сколько ошибок можно пропустить.
    # Это позволяет попробовать все типы из Union перед тем, как выбросить исключение.
    skip_error = len(rtypes) - 1

    for rtype in rtypes:
        # Проверяем, ожидается ли список элементов
        origin = get_origin(rtype)
        many = origin is list
        if many:
            # Если ожидается список, извлекаем тип элементов списка
            rtype = get_args(rtype)[0]

        # Проверяем, является ли ожидаемый тип Pydantic моделью
        if isinstance(rtype, type) and issubclass(rtype, BaseModel):
            try:
                if many:
                    # Если ожидается список моделей, применяем parse_obj к каждому элементу
                    return [rtype.model_validate(d) for d in data]
                else:
                    # Если ожидается одна модель, применяем parse_obj ко всем данным
                    return rtype.model_validate(data)
            except ValidationError as e:
                # Если возникла ошибка валидации, проверяем, можно ли её пропустить
                if skip_error:
                    # Если можно пропустить, уменьшаем счетчик и продолжаем цикл
                    skip_error -= 1
                else:
                    # Если пропустить нельзя, выбрасываем исключение
                    raise e
        # Есои не указана схема, то не пытаемся делать конвертацию типов
        else:
            break

    # Если ни одна конвертация не удалась или не требовалась, возвращаем исходные данные
    return data

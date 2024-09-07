"""
Модуль для работы со временем и временными зонами
"""

from datetime import datetime

import pytz
from fastapi import FastAPI

moscow_tz = pytz.timezone("Europe/Moscow")
new_york_tz = pytz.timezone("America/New_York")


def get_datetime_now(app: FastAPI) -> datetime:
    """Получить текущие время с учетом тайм зоны

    # Установка врменной зоны для проекта
    app.state.TIMEZONE = moscow_tz
    """
    return datetime.now(app.state.TIMEZONE)

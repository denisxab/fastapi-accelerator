"""Во время работы программы, эти значения заполняться один раз из request.app"""

import pytz

from fastapi_accelerator.utils import singleton


@singleton
def DEBUG(app=None) -> bool:
    return app.debug


@singleton
def CACHE_STATUS(app=None) -> bool:
    return app.state.CACHE_STATUS


@singleton
def DATABASE_MANAGER(app=None):
    return app.state.DATABASE_MANAGER


@singleton
def AUTH_JWT(app=None):
    return app.state.auth_jwt


@singleton
def TIMEZONE(app=None) -> pytz.timezone:
    return app.state.TIMEZONE

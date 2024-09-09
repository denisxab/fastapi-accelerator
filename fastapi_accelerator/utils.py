class SingletonMeta(type):
    """Мета класс для реализации паттерна Одиночка"""

    instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls.instance


def singleton(func):
    """Декоратор для реализации паттерна Одиночка

    Пример использования:

        @singleton
        def CACHE_STATUS(app=None) -> bool:
            return app.state.CACHE_STATUS

        cache_status = CACHE_STATUS() or CACHE_STATUS(request.app)
    """

    instance = None

    def wrapper(*args, **kwargs):
        nonlocal instance
        if instance is not None:
            return instance
        if instance is None and (not args and not kwargs):
            return False
        if instance is None:
            instance = func(*args, **kwargs)
        return instance

    return wrapper

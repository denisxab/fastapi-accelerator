class SingletonMeta(type):
    """Мета класс для реализации паттерна Одиночка"""

    instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls.instance

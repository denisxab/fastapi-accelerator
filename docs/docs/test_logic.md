## Зачем и как писать тесты

Рассмотрим тестирование: REST API, использующего реляционную СУБД и возвращающего ответы в формате JSON.

Это один из наиболее распространенных подходов к интеграционному тестированию, который эмулирует ручную проверку API методов. Такой подход позволяет покрыть значительную часть бизнес-логики тестами, поэтому автоматизация тестирования API – хороший старт. Эти тесты не только воспроизводят ручное тестирование, но и позволяют проверять побочные эффекты в базе данных, такие как создание новых записей после выполнения POST-запросов.

Реализовать такие тесты в `Django` достаточно просто благодаря встроенным инструментам, однако в `FastAPI` эта задача требует большего внимания. Поэтому я разработал компоненты, которые позволяют создавать интеграционные тесты API на `FastAPI` так же удобно и быстро, как и в `Django`.

## Предварительная настройка для тестирования

1. Установка

```bash
poetry add pytest pytest-asyncio httpx
```

2. Создать файл `app/pytest.ini`

```ini
[pytest]
; Доп аргументы к запуску
addopts = -v -l -x -s --lf --disable-warnings

; Маска для поиска файлов с тестами
python_files = tests.py test_*.py *_tests.py

; Позволяет выводить логи (logs) в консоль при запуске тестов.
log_cli = true
```

3. Создать файл `app/conftest.py`

```python
from app.core.config import TEST_DATABASE_URL
from fastapi_accelerator.db.dbsession import MainDatabaseManager

# Вы можете указать точный список импорта, это для простоты мы импортируем все
from fastapi_accelerator.testutils import *  # noqa E402

# Нужно создать менеджер БД до импорта APP
# чтобы паттерн одиночка создал только тестовое instance
# и в APP уже взялся тестовый instance
TestDatabaseManager = MainDatabaseManager(
    TEST_DATABASE_URL, echo=False, DEV_STATUS=True
)

from main import app  # noqa E402

# Отключить кеширование во время тестов
app.state.CACHE_STATUS = False

SettingTest(TestDatabaseManager, app, alembic_migrate=True, keepdb=True) # noqa F405
```

## Основные компоненты для тестирования

Для упрощения написания тестов, их стандартизацию, вы можете использовать следующие компоненты:

-   Фикстуры:

    -   `client` - Клиент для выполнения тестовых API запросов
    -   `test_app` - Тестовое FastAPI приложение
    -   `url_path_for` - Получить полный URL путь, по имени функции обработчика
    -   `engine` - Синхронный двигатель
    -   `aengine` - Асинхронный двигатель
    -   `db_session` - Соединение с тестовой БД
    -   `db_manager` - Менеджер с тестовой БД

-   Функции:

    -   `check_response_json` - Функция, которая объединяет основные проверки для API ответа
    -   `rm_key_from_deep_dict` - Функция для отчистить не нужные ключи у API ответа

-   Классы:

    -   `BasePytest` - Базовый класс для тестирования через классы
    -   `BaseAuthJwtPytest` - Добавление аутентификации по JWT(`@client_auth_jwt`) для `BasePytest`

-   Контекстный менеджер:

    -   `track_queries` - Перехват выполняемых SQL команд, во время контекста, для последующего анализ - например подсчёта количества.

-   Декораторы:

    -   `@apply_fixture_db(ФункцияВозвращающаяФикстуры)` - Декоратор, который добавляет фикстуры в БД перед тестом и удаляет их после теста.
    -   `@client_auth_jwt()` - Декоратор который аутентифицирует тестового клиента по JWT.
    -   `@patch_integration(ПравилаПодмены)` - Декоратор который подменяет методы интеграций на Mock функции.

## Подробнее про компоненты для тестирования

### Fixture - `client`

Основная фикстура для выполнения тестовых API запросов.

Порядок работы фикстуры `client`:

-   Этапы на уровней всей тестовой сессии:

    1. (before) Создастся тестовая БД если её нет;
    2. (before) В зависимости от настройки `SettingTest.alembic_migrate`;

        - Если `True` -> Создаст таблицы через миграции `alembic`
        - Если `False` -> Создаст таблицы через `create_all()`

    3. (after) После завершение всех тестов, в зависимости от настройки `SettingTest.keepdb`;
        - Если `True` -> Ничего
        - Если `False` -> Удаляться все таблицы из тестовой БД

-   Этапы на уровней каждого тестового функции/метода:

    3. В тестовую функцию/метода попадает аргумент `client: TestClient`;
    4. (after) После выхода из тестовой функции/метода, все данных во всех таблицах отчищаются(кроме таблицы `alembic_version`, так как саму БД мы не удаляем);

```python
from fastapi.testclient import TestClient

def test_имя(client: TestClient):
    response = client.get('url')
```

### Decorator - `@client_auth_jwt`

На практике нам часто приходиться тестировать API методы которые требуют аутентификацию. Делать обход аутентификации в тестах плохой вариант, так как можно упустить некоторые исключения, или логику API метода которая завязана на данных аутентифицированного пользователя. Поэтому чтобы аутентифицировать тестового клиента, укажите декоратор `@client_auth_jwt` для тестовой функции/метода

-   Пример использование декоратора для тестовой функции:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt

@client_auth_jwt(username='test')
def test_имя(client: TestClient):
    print(client.headers['authorization']) # 'Bearer ...'
```

-   Пример использование декоратора для тестового метода в классе `BasePytest`:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt

class TestИмяКласса(BasePytest):

    @client_auth_jwt()
    def test_имя(self, client: TestClient):
        print(client.headers['authorization']) # 'Bearer ...'
```

> Если вы используете декоратор `@client_auth_jwt` в классе `BasePytest`, то он возьмет `username` из `self.TEST_USER['username']`, этот атрибут уже определен в `BasePytest` и равен по умолчанию `test`.

### Decorator - `@apply_fixture_db`

Идея взята из тестирования `Django`, в котором можно указать в атрибуте `fixtures` список файлов с фикстурами, которые будут загружены для тестов, и удалены после окончания. Этот очень удобно для переиспользовать тестовых данных.

Но я решил модифицировать этот вариант и сделать фикстуры не в виде `JSON` а виде объектов `SqlAlchemy`. Использование `JSON` лучше когда нужно переносить эти данные на другие платформы, но такое встречается редко, чаще всего фикстуры для backend тестов используются только на backend, и горазда удобнее и быстрее писать в формате объектов БД, чем в формате `JSON`. Поэтому выбран формат объектов.

Порядок работы декоратора `@apply_fixture_db`:

1. Получает записи из переданной функции `export_func`;
2. Создает записи в БД;
3. Выполняется тестовая функция. Если она ожидает аргумент `fixtures`, то в него передадутся записи из `export_func`;
4. Удаляет записи из БД:
    - Если вы используете фикстуру `client`, то она автоматически отчистить все данные в таблицах, после выполнения тестовой функции.
    - Если вы не используете фикстуру `client`, то для отчистки данных укажите в декоратор аргумент `flush=True`

---

-   Оформление файлами с тестовыми данными `app.fixture.items_v1.py`:

```python
from fastapi_accelerator.utils import to_namedtuple
from app.models.timemeasurement import Task, TaskExecution, TaskUser

def export_fixture_task():
    # Создание пользователей и задач
    user1 = TaskUser(id=0, name="Alice")
    user2 = TaskUser(id=1, name="Bob")

    task1 = Task(id=9, name="Admins")
    task2 = Task(id=8, name="Users")

    # Связывание пользователей с задачами
    user1.tasks.append(task1)
    user2.tasks.append(task1)
    user2.tasks.append(task2)

    # Вернуть именований картеж
    return to_namedtuple(
        user1=user1,
        user2=user2,
        task1=task1,
        task2=task2,
        task_execution1=TaskExecution(
            id=91,
            task=task1,
            start_time="2024-09-06T10:55:43",
            end_time="2024-09-06T10:59:43",
        ),
    )
```

-   Использование декоратора в тестовых функциях:

```python
from fastapi_accelerator.test_utils import apply_fixture_db
from app.fixture.items_v1 import export_fixture_task

@apply_fixture_db(export_fixture_task)
def test_имя(client: TestClient):
    response = client.get('url')
```

-   Использование декоратора в тестовых методах, в этом варианте вы можно указывать только для `setUp`, тогда он будет применен для всех тестовых методов:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest
from fastapi_accelerator.test_utils import apply_fixture_db
from app.fixture.items_v1 import export_fixture_task

class TestИмяКласса(BasePytest):

    @apply_fixture_db(export_fixture_task)
    def setUp(self, fixtures: NamedTuple):
        self.fixtures = fixtures

    def test_имя(self, client: TestClient):
        response = client.get('url')
        print(self.fixtures)
```

### Decorator - `@patch_integration`

Тестирование интеграций с внешними API

Самым сложным аспектом тестирования являются интеграции с внешними API, поскольку во время тестов необходимо избегать выполнения реальных запросов к этим API. Поэтому нам приходится самостоятельно разрабатывать логику для имитации работы внешнего API. Хотя наша имитация может не полностью отражать реальную работу API, это все же лучше, чем игнорировать интеграцию.

В командах часто каждый разработчик создает свои собственные моки для интеграций, что приводит к путанице и отсутствию единого стандарта. Существует высокая вероятность ошибок, когда мок может не сработать, и произойдет отправка запроса в реальный API.

Для решения этой проблемы мы используем классы интеграции `EndpointsDeclaration` с декоратором `@integration.endpoint`, что позволяет создать единую точку входа, которую можно легко заменить во время тестирования и исключить возможность выполнения реального метода интеграции.

Пример тестирования метода `FastAPI`, который вызывает метод интеграции:

-   Обработчик FastAPI:

```python
@router.get("/translate")
async def translate_api(
    text: str, from_lang: str = "en", to_lang: str = "ru"
) -> GoogleTranslateEndpoints.Schema.TranslateV2:
    # Вызвать метод интеграции
    return await gtapi.translate(text, from_lang, to_lang)
```

-   `test_имя.py` пример интеграции с `google` переводчик:

```python
from fastapi_accelerator.testutils.fixture_integration import patch_integration
from app.integration.google_translate.mock import google_translate_mock_rules

# Правила подмены методов интеграции на mock.
# Если в коде вызывается интеграция, которая не указана в mock_rules, возникает исключение.
# Это предотвращает случайные реальные запросы, если вы забыли указать mock.
@patch_integration(mock_rules=google_translate_mock_rules)
def test_integration_google_translate(client: TestClient, url_path_for: Callable):
    # Выполнение тестового запроса
    response = client.get(
        url_path_for("translate_api"),
        params=dict(text="Hello", from_lang="en", to_lang="ru"),
    )
    # Проверка ответа
    assert response.json() == {"text": "Привет"}
```

> Значение для `mock_rules` можно использовать откуда угодно, но рекомендую хранить и брать из `app/integration/ПакетИнтеграции/mock.py`

-   Рекомендуется хранить подменные функции в одном пакете с интеграцией в `app/integration/ПакетИнтеграции/mock.py`, чтобы при импорте этого пакета в другой проект также можно было использовать функции из `mock.py`, не создавая свои имитации.

```python
from app.integration.google_translate.endpoint import GoogleTranslateEndpoints
from fastapi_accelerator.integration.http_integration import ApiHTTP
from fastapi_accelerator.testutils.fixture_integration import MockRules


async def overwrite_translate(api: ApiHTTP, *args, **kwargs):
    # Удобный вариант имитации, когда через match аргументов, возвращаем определенный ответ.
    match args:
        case ("hello", "en", "ru"):
            return {"text": "Привет"}
    return None


# Правила замены методов интеграции на mock
google_translate_mock_rules = MockRules(
    # Реальный метод интеграции: замена на mock функцию
    {GoogleTranslateEndpoints.translate: overwrite_translate}
)
```

> К мок-функциям применяются те же требования к формату ответа, что и к реальному методу интеграции.

### Context manager - `track_queries`

Идея взята из тестирования `Django` метода `self.assertNumQueries`, который поваляет проверять количество выполненных SQL команд в контексте. Это очень полезно когда используется ORM, который может из за неаккуратного использования, генерировать сотни SQL команд. Поэтому лучше у каждого вызова тестового API метода отлеживать количество выполненных SQL команд.

-   Пример использования контекстного менеджера `track_queries`:

```python
from fastapi_accelerator.testutils.fixture_db.trace_sql import track_queries

def test_имя(client: TestClient, db_manager: MainDatabaseManager):
    with track_queries(db_manager, expected_count=3):
        response = client.get('url')
```

-   Вы можете получить полный список выполненных SQL команд из `tracker.queries`:

```python
from fastapi_accelerator.testutils.fixture_db.trace_sql import track_queries

def test_имя(client: TestClient, db_manager: MainDatabaseManager):
    with track_queries(db_manager) as tracker:
        response = client.get('url')

    # Если количество измениться, то выведется список всех выполненных SQL команд
    assert tracker.count == 3, tracker.queries
```

### Func - `check_response_json`

По опыту написания тестов, могу выделить несколько основных проверок для ответов API JSON.

1. Проверить статус ответа
2. Получить ответ в формате JSON
3. Если нужно, то удалить динамические ключи из ответа, например дату создания, дату обновления, первичный ключ новой записи. Работает через функцию `rm_key_from_deep_dict`
4. Сравнить ответ с ожидаемым

Эти проверки выполняются в функции `check_response_json`

Пример использования:

```python
def test_имя(client: TestClient):
    response = client.post('url', json={...})
    check_response_json(
        response,
        200,
        {
            "page": 1,
            "size": 10,
            "count": 1,
            "items": [
                {
                    "end_time": "2024-09-06T10:59:43",
                    "start_time": "2024-09-06T10:55:43",
                    "task": {
                        "description": None,
                        "name": "Admins",
                    },
                }
            ],
        },
        exclude_list=['id','task_id']
    )
```

### Тестирование через классы

#### Класс `BasePytest`

Удобнее и понятнее, создавать логически связанные тесты в одном классе, и указывать в методе `setUp` общую для них инициализацию, например общий url, или создание тестовых объектов в БД, или создание переменных хранящих ожидаемый JSON ответ.

-   Пример создания класса для тестирования на основание `BasePytest`:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest

class TestИмяКласса(BasePytest):

    def setUp(self):
        # Метод для выполнения необходимой настройки перед каждым тестом.
        ...

    def test_имя(self, client: TestClient):
        ...
```

-   Вы можете использовать фикстуры и декораторы для тестовых методах, например аутентификаций по JWT:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt

class TestИмяКласса(BasePytest):

    def setUp(self):
        # Метод для выполнения необходимой настройки перед каждым тестом.
        ...

    @client_auth_jwt()
    def test_имя(self, client: TestClient):
        print(client.headers['authorization']) # 'Bearer ...'
        ...
```

#### Класс `BaseAuthJwtPytest`

Чтобы не писать для каждого тестового метода в классе, декоратор `@client_auth_jwt` вы можете наследоваться от `BaseAuthJwtPytest`, в котором эта логика уже реализована.

-   Пример создания класса для тестирования на основание `BaseAuthJwtPytest`:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BaseAuthJwtPytest

class TestИмяКласса(BaseAuthJwtPytest):

    def setUp(self):
        # Метод для выполнения необходимой настройки перед каждым тестом.
        ...

    def test_имя(self, client: TestClient):
        print(client.headers['authorization']) # 'Bearer ...'
        ...
```

## Примеры тестов

### Классическая тестовой функции

Проверки REST API метода, который использует РСУБД, и возвращает ответ в формате `JSON`:

```python
from typing import Callable, NamedTuple

from fastapi.testclient import TestClient

from app.fixture.items_v1 import export_fixture_file
from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.testutils import apply_fixture_db, client_auth_jwt, track_queries, check_response_json

# Аутентифицировать тестового клиента
@client_auth_jwt(username="test")
# Создать тестовые данных из функции с фикстурами
@apply_fixture_db(export_fixture_file)
def test_имя(
    client: TestClient,  # Тестовый клиент для API запросов
    url_path_for: Callable,  # Функция для получения url по имени функции обработчика
    db_manager: MainDatabaseManager,  # Менеджер тестовой БД
    fixtures: NamedTuple,  # Хранит созданные данные из фикстур
):
    # Проверка количество выполняемых SQL команд
    with track_queries(db_manager, expected_count=3):
        # Запрос в API
        response = client.get(url_path_for("ИмяФункции"))
    # Проверка JSON API ответа
    check_response_json(
        response,
        200,
        {
            "id": fixtures.Имя.id,
        },
    )
    # TODO Можно для методов POST, UPDATE, DELETE добавить проверку на изменения записей в БД.
    ...
```

### Классический тестовый класс

Проверки REST API метода, который использует РСУБД, и возвращает ответ в формате `JSON`:

```python
from typing import Callable, NamedTuple

from fastapi.testclient import TestClient

from app.fixture.items_v1 import export_fixture_file
from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.testutils import apply_fixture_db
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt
from fastapi_accelerator.testutils.fixture_db.trace_sql import track_queries
from fastapi_accelerator.testutils.utils import BaseAuthJwtPytest, check_response_json

BASE_URL_V1 = "/api/v1/"

class TestИмя(BaseAuthJwtPytest):

    # Создать тестовые данных из функции с фикстурами
    @apply_fixture_db(export_fixture_file)
    def setUp(self, fixtures: NamedTuple):
        self.url = BASE_URL_V1 + "taskexecution"
        self.fixtures = fixtures # Хранит созданные данные из фикстур

    def test_имя(self, client: TestClient, db_manager: MainDatabaseManager):
        # Проверка количество выполняемых SQL команд
        with track_queries(db_manager, expected_count=3):
            # Запрос в API
            response = client.get(self.url)
        # Проверка JSON API ответа
        check_response_json(
            response,
            200,
            {
                "id": self.fixtures.Имя.id,
            },
        )
        # TODO Можно для методов POST, UPDATE, DELETE добавить проверку на изменения записей в БД.
        ...
```

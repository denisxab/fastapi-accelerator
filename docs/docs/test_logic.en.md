## Why and how to write tests

Let's consider testing: a REST API that uses a relational DBMS and returns responses in JSON format. This is one of the most common approaches to integration testing, which emulates manual checking of API methods. This approach allows covering a significant part of business logic with tests, so automating API testing is a good start. These tests not only reproduce manual testing but also allow checking side effects in the database, such as creating new records after executing POST requests. Implementing such tests in `Django` is quite simple thanks to built-in tools, however, in `FastAPI`, this task requires more attention. Therefore, I developed components that allow creating integration API tests on `FastAPI` as conveniently and quickly as in `Django`.

## Preliminary setup for testing

1. Installation

```bash
poetry add pytest pytest-asyncio httpx
```

2. Create file `app/pytest.ini`

```ini
[pytest]
; Additional arguments for running
addopts = -v -l -x -s --lf --disable-warnings
; Mask for searching test files
python_files = tests.py test_*.py *_tests.py
; Allows outputting logs to the console when running tests
log_cli = true
```

3. Create file `app/conftest.py`

```python
from app.core.config import TEST_DATABASE_URL
from fastapi_accelerator.db.dbsession import MainDatabaseManager
# You can specify an exact import list, for simplicity we import everything
from fastapi_accelerator.testutils import * # noqa E402

# Need to create DB manager before importing APP
# so that the singleton pattern creates only a test instance
# and APP already takes the test instance
TestDatabaseManager = MainDatabaseManager(
    TEST_DATABASE_URL,
    echo=False,
    DEV_STATUS=True
)

from main import app # noqa E402

# Disable caching during tests
app.state.CACHE_STATUS = False

SettingTest(TestDatabaseManager, app, alembic_migrate=True, keepdb=True) # noqa F405
```

## Main components for testing

To simplify writing tests, standardize them,... you can use the following components:

-   Fixtures:

    -   `client` - Client for executing test API requests
    -   `test_app` - Test FastAPI application
    -   `url_path_for` - Get full URL path by handler function name
    -   `engine` - Synchronous engine
    -   `aengine` - Asynchronous engine
    -   `db_session` - Connection to test DB
    -   `db_manager` - Manager with test DB

-   Functions:

    -   `check_response_json` - Function that combines main checks for API response
    -   `rm_key_from_deep_dict` - Function to clean unnecessary keys from API response

-   Classes:

    -   `BasePytest` - Base class for testing through classes
    -   `BaseAuthJwtPytest` - Adding JWT authentication (`@client_auth_jwt`) for `BasePytest`

-   Context manager:

    -   `track_queries` - Intercept executed SQL commands during the context for subsequent analysis - for example, counting.

-   Decorators:
    -   `@apply_fixture_db(FunctionReturningFixtures)` - Decorator that adds fixtures to DB before test and removes them after test.
    -   `@client_auth_jwt()` - Decorator that authenticates test client by JWT.
    -   `@patch_integration(ReplacementRules)` - Decorator that replaces integration methods with Mock functions.

## More about testing components

### Fixture - `client`

The main fixture for executing test API requests.

The order of work for the `client` fixture:

-   Stages at the level of the entire test session:

1. (before) Test DB will be created if it doesn't exist;
2. (before) Depending on the `SettingTest.alembic_migrate` setting;
    - If `True` -> Will create tables through `alembic` migrations
    - If `False` -> Will create tables through `create_all()`
3. (after) After completing all tests, depending on the `SettingTest.keepdb` setting;
    - If `True` -> Nothing
    - If `False` -> All tables from the test DB will be deleted

-   Stages at the level of each test function/method:

3. The test function/method receives the argument `client: TestClient`;
4. (after) After exiting the test function/method, all data in all tables is cleared (except the `alembic_version` table, as we don't delete the DB itself);

```python
from fastapi.testclient import TestClient

def test_name(client: TestClient):
    response = client.get('url')
```

### Decorator - `@client_auth_jwt`

In practice, we often have to test API methods that require authentication. Bypassing authentication in tests is a bad option, as some exceptions or API method logic tied to authenticated user data may be missed. Therefore, to authenticate the test client, specify the `@client_auth_jwt` decorator for the test function/method

-   Example of using the decorator for a test function:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt

@client_auth_jwt(username='test')
def test_name(client: TestClient):
    print(client.headers['authorization']) # 'Bearer ...'
```

-   Example of using the decorator for a test method in the `BasePytest` class:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt

class TestClassName(BasePytest):
    @client_auth_jwt()
    def test_name(self, client: TestClient):
        print(client.headers['authorization']) # 'Bearer ...'
```

> If you use the `@client_auth_jwt` decorator in the `BasePytest` class, it will take `username` from `self.TEST_USER['username']`, this attribute is already defined in `BasePytest` and equals `test` by default.

### Decorator - `@apply_fixture_db`

The idea is taken from `Django` testing, where you can specify in the `fixtures` attribute a list of files with fixtures that will be loaded for tests and removed after completion. This is very convenient for reusing test data. But I decided to modify this option and make fixtures not in `JSON` format but in the form of `SqlAlchemy` objects. Using `JSON` is better when you need to transfer this data to other platforms, but this is rare, most often fixtures for backend tests are used only on the backend,... and it's much more convenient and faster to write in the format of DB objects than in `JSON` format. Therefore, the object format was chosen.

The order of work for the `@apply_fixture_db` decorator:

1. Gets records from the passed `export_func` function;
2. Creates records in the DB;
3. The test function is executed. If it expects a `fixtures` argument, it will be passed records from `export_func`;
4. Deletes records from the DB:
    - If you use the `client` fixture, it will automatically clear all data in the tables after executing the test function.
    - If you don't use the `client` fixture, specify the `flush=True` argument in the decorator for data clearing.

---

-   Formatting files with test data `app.fixture.items_v1.py`:

```python
from fastapi_accelerator.utils import to_namedtuple
from app.models.timemeasurement import Task, TaskExecution, TaskUser

def export_fixture_task():
    # Creating users and tasks
    user1 = TaskUser(id=0, name="Alice")
    user2 = TaskUser(id=1, name="Bob")
    task1 = Task(id=9, name="Admins")
    task2 = Task(id=8, name="Users")

    # Linking users with tasks
    user1.tasks.append(task1)
    user2.tasks.append(task1)
    user2.tasks.append(task2)

    # Return named tuple
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

-   Using the decorator in test functions:

```python
from fastapi_accelerator.test_utils import apply_fixture_db
from app.fixture.items_v1 import export_fixture_task

@apply_fixture_db(export_fixture_task)
def test_name(client: TestClient):
    response = client.get('url')
```

-   Using the decorator in test methods, in this case you can specify only for `setUp`, then it will be applied to all test methods:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest
from fastapi_accelerator.test_utils import apply_fixture_db
from app.fixture.items_v1 import export_fixture_task

class TestClassName(BasePytest):
    @apply_fixture_db(export_fixture_task)
    def setUp(self, fixtures: NamedTuple):
        self.fixtures = fixtures

    def test_name(self, client: TestClient):
        response = client.get('url')
        print(self.fixtures)
```

### Decorator - `@patch_integration`

Testing integrations with external APIs

The most difficult aspect of testing is integrations with external APIs, as during tests we need to avoid executing real requests to these APIs. Therefore, we have to develop logic ourselves to simulate the work of the external API. Although our simulation may not fully reflect the real work of the API, it's still better than ignoring the integration. In teams, often each developer creates their own mocks for integrations, which leads to confusion and lack of a single standard. There is a high probability of errors when the mock may not work, and a request will be sent to the real API.

To solve this problem, we use integration classes `EndpointsDeclaration` with the `@integration.endpoint` decorator, which allows creating a single entry point that can be easily replaced during testing and exclude the possibility of executing the real integration method.

Example of testing a `FastAPI` method that calls an integration method:

-   FastAPI handler:

```python
@router.get("/translate")
async def translate_api(
    text: str,
    from_lang: str = "en",
    to_lang: str = "ru"
) -> GoogleTranslateEndpoints.Schema.TranslateV2:
    # Call integration method
    return await gtapi.translate(text, from_lang, to_lang)
```

-   `test_name.py` example of integration with `google` translator:

```python
from fastapi_accelerator.testutils.fixture_integration import patch_integration
from app.integration.google_translate.mock import google_translate_mock_rules

# Rules for replacing integration methods with mock.
# If an integration is called in the code that is not specified in mock_rules, an exception occurs.
# This prevents accidental real requests if you forgot to specify a mock.
@patch_integration(mock_rules=google_translate_mock_rules)
def test_integration_google_translate(client: TestClient, url_path_for: Callable):
    # Executing test request
    response = client.get(
        url_path_for("translate_api"),
        params=dict(text="Hello", from_lang="en", to_lang="ru"),
    )
    # Checking response
    assert response.json() == {"text": "Привет"}
```

> The value for `mock_rules` can be used from anywhere, but I recommend storing and taking it from `app/integration/IntegrationPackage/mock.py`

-   It's recommended to store replacement functions in the same package with integration in `app/integration/IntegrationPackage/mock.py`, so that when importing this package into another project, you can also use functions from `mock.py` without creating your own imitations.

```python
from app.integration.google_translate.endpoint import GoogleTranslateEndpoints
from fastapi_accelerator.integration.http_integration import ApiHTTP
from fastapi_accelerator.testutils.fixture_integration import MockRules

async def overwrite_translate(api: ApiHTTP, *args, **kwargs):
    # Convenient imitation option when through match of arguments, we return a certain response.
    match args:
        case ("hello", "en", "ru"):
            return {"text": "Привет"}
    return None

# Rules for replacing integration methods with mock
google_translate_mock_rules = MockRules(
    # Real integration method: replacement with mock function
    {GoogleTranslateEndpoints.translate: overwrite_translate}
)
```

> The same requirements for response format apply to mock functions as to the real integration method.

### Context manager - `track_queries`

The idea is taken from `Django` testing method `self.assertNumQueries`, which allows checking the number of executed SQL commands in the context. This is very useful when using ORM, which can generate hundreds of SQL commands due to careless use. Therefore, it's better to track the number of executed SQL commands for each test API method call.

-   Example of using the `track_queries` context manager:

```python
from fastapi_accelerator.testutils.fixture_db.trace_sql import track_queries

def test_name(client: TestClient, db_manager: MainDatabaseManager):
    with track_queries(db_manager, expected_count=3):
        response = client.get('url')
```

-   You can get a full list of executed SQL commands from `tracker.queries`:

```python
from fastapi_accelerator.testutils.fixture_db.trace_sql import track_queries

def test_name(client: TestClient, db_manager: MainDatabaseManager):
    with track_queries(db_manager) as tracker:
        response = client.get('url')
        # If the number changes, a list of all executed SQL commands will be displayed
        assert tracker.count == 3, tracker.queries
```

### Func - `check_response_json`

From experience in writing tests, I can highlight several main checks for API JSON responses.

1. Check response status
2. Get response in JSON format
3. If needed, remove dynamic keys from the response, for example creation date, update date, primary key of a new record. Works through the `rm_key_from_deep_dict` function
4. Compare the response with the expected one

These checks are performed in the `check_response_json` function

Example of use:

```python
def test_name(client: TestClient):
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
                },
            ],
        },
        exclude_list=['id','task_id']
    )
```

### Testing through classes

#### Class `BasePytest`

It's more convenient and understandable to create logically related tests in one class, and specify common initialization for them in the `setUp` method, for example, a common URL, or creation of test objects in the database, or creation of variables storing the expected JSON response.

-   Example of creating a test class based on `BasePytest`:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest

class TestClassName(BasePytest):

    def setUp(self):
        # Method for performing necessary setup before each test.
        ...

    def test_name(self, client: TestClient):
        ...
```

-   You can use fixtures and decorators for test methods, for example, JWT authentication:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BasePytest
from fastapi_accelerator.testutils.fixture_auth import client_auth_jwt

class TestClassName(BasePytest):

    def setUp(self):
        # Method for performing necessary setup before each test.
        ...

    @client_auth_jwt()
    def test_name(self, client: TestClient):
        print(client.headers['authorization']) # 'Bearer ...'
        ...
```

#### Class `BaseAuthJwtPytest`

To avoid writing the `@client_auth_jwt` decorator for each test method in the class, you can inherit from `BaseAuthJwtPytest`, which already implements this logic.

-   Example of creating a test class based on `BaseAuthJwtPytest`:

```python
from fastapi.testclient import TestClient
from fastapi_accelerator.testutils.fixture_base import BaseAuthJwtPytest

class TestClassName(BaseAuthJwtPytest):

    def setUp(self):
        # Method for performing necessary setup before each test.
        ...

    def test_name(self, client: TestClient):
        print(client.headers['authorization']) # 'Bearer ...'
        ...
```

## Test Examples

### Classic test function

Checking a REST API method that uses RDBMS and returns a response in `JSON` format:

```python
from typing import Callable, NamedTuple

from fastapi.testclient import TestClient

from app.fixture.items_v1 import export_fixture_file
from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.testutils import apply_fixture_db, client_auth_jwt, track_queries, check_response_json

# Authenticate test client
@client_auth_jwt(username="test")
# Create test data from fixture function
@apply_fixture_db(export_fixture_file)
def test_name(
    client: TestClient,  # Test client for API requests
    url_path_for: Callable,  # Function to get URL by handler function name
    db_manager: MainDatabaseManager,  # Test DB manager
    fixtures: NamedTuple,  # Stores created data from fixtures
):
    # Check the number of executed SQL commands
    with track_queries(db_manager, expected_count=3):
        # API request
        response = client.get(url_path_for("FunctionName"))
    # Check JSON API response
    check_response_json(
        response,
        200,
        {
            "id": fixtures.Name.id,
        },
    )
    # TODO For POST, UPDATE, DELETE methods, you can add a check for changes in DB records.
    ...
```

### Classic test class

Checking a REST API method that uses RDBMS and returns a response in `JSON` format:

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

class TestName(BaseAuthJwtPytest):

    # Create test data from fixture function
    @apply_fixture_db(export_fixture_file)
    def setUp(self, fixtures: NamedTuple):
        self.url = BASE_URL_V1 + "taskexecution"
        self.fixtures = fixtures # Stores created data from fixtures

    def test_name(self, client: TestClient, db_manager: MainDatabaseManager):
        # Check the number of executed SQL commands
        with track_queries(db_manager, expected_count=3):
            # API request
            response = client.get(self.url)
        # Check JSON API response
        check_response_json(
            response,
            200,
            {
                "id": self.fixtures.Name.id,
            },
        )
        # TODO For POST, UPDATE, DELETE methods, you can add a check for changes in DB records.
        ...
```

# Home

![log](./images/logo.png)

## Accelerating Development with FastAPI: Powerful Toolkit for Creating and Testing APIs

In the world of modern web development, FastAPI has established itself as a powerful and fast framework for creating APIs. However, when working on large projects, developers often face the need to optimize routine processes, improve code structure, and simplify testing. In this article, we will look at a set of tools that will help solve these problems and significantly speed up development with FastAPI.

While attending numerous interviews, I noticed that many companies actively using FastAPI have developed their own libraries, but there are practically no similar tools with open access and free licenses. As an experienced Python and Django backend developer, I decided to adapt and integrate the most useful and in-demand solutions for developing REST APIs in FastAPI, based on my experience working with Django.

Short-term goal: gather feedback from the community about this idea.
Long-term goal: improve the tool in open source, encouraging large companies to abandon the development and support of their own proprietary code. Instead, we aim to create an ecosystem where companies not only use common tools but also actively participate in their improvement, contributing to the open-source project.

-   https://github.com/denisxab/fastapi_accelerator
-   https://pypi.org/project/fastapi_accelerator

## Who will find this useful?

-   Python backend developers using or planning to use FastAPI
-   Teams working on medium and large projects with FastAPI
-   Developers who want to improve the structure of their FastAPI projects and speed up the development process
-   Those looking for effective tools for testing FastAPI applications

## Why is this toolkit needed?

FastAPI Accelerator is an open-source toolkit created based on best practices for REST API development. The main goal of the presented toolkit is to accelerate and simplify the development of projects on FastAPI. This is achieved by:

1. Detailed and good documentation.
2. Providing reusable code for typical tasks.
3. Implementing a universal manager for working with RDBMS.
4. Implementing ViewSet for quickly creating views with basic business logic.
5. Integrating JWT authentication.
6. Simplifying writing and executing integration tests for APIs.
7. Optimizing work with Alembic for managing migrations in production and test environments.
8. Standardizing architecture for HTTP integrations.

All these components are interconnected and complement each other, automating routine tasks.

## Tool Structure

Let's look at the main components of our toolkit:

```bash
fastapi_accelerator/
├── db/ # Logic for interacting with RDBMS
├── pattern/ # Templates for projects
├── testutils/ # Utilities for testing FastAPI
├── integration/ # Utilities for integrations with external systems
├── commands/ # CLI commands
├── cache.py # Caching implementation
├── auth_jwt.py # JWT authentication
├── exception.py # Exception handling
├── middleware.py # Middleware components
├── paginator.py # Pagination implementation
├── timezone.py # Working with time zones
├── viewset.py # ViewSet implementation
└── utils.py # General utilities
```

## Connecting to FastAPI

File `main.py`:

```python
from fastapi import FastAPI
from fastapi_accelerator.pattern.pattern_fastapi import base_pattern
from app.core.config import BASE_DIR_PROJECT, DEBUG, SECRET_KEY
from fastapi_accelerator.timezone import moscow_tz
from app.core.db import DatabaseManager
from app.core.security import AuthJWT
import app.api.v1.router as RouterV1

app = FastAPI()

# Pattern for the project
base_pattern(
    app,
    routers=(RouterV1.router,),
    timezone=moscow_tz,
    cache_status=True,
    debug=DEBUG,
    base_dir=BASE_DIR_PROJECT,
    database_manager=DatabaseManager,
    secret_key=SECRET_KEY,
    # Connect JWT authentication
    AuthJWT.mount_auth(app)
)
```

## Main Components

### Base Pattern

The `base_pattern` function adds many useful functions to `app`, including:

-   Filling `state` and other information in `app`.
-   Resolving `CORS`.
-   Connecting routers with `ViewSet` support.
-   Adding a `healthcheck` method.
-   `Middleware` for debugging API request execution time.
-   Detailed output for `HTTP` exceptions.

### DatabaseManager

`DatabaseManager` is a universal tool for working with RDBMS, providing both synchronous and asynchronous (names starting with `a`) methods. `DatabaseManager` uses the singleton pattern, so it can be easily substituted in tests.

Usage example:

```python
from app.core.config import DATABASE_URL, DEBUG, DEV_STATUS
from fastapi_accelerator.dbsession import MainDatabaseManager

DatabaseManager = MainDatabaseManager(DATABASE_URL, echo=DEBUG, DEV_STATUS=DEV_STATUS)
```

-   General characteristics

    -   `DEV_STATUS` - Development mode indicator. When `DEV_STATUS=False`, it blocks the execution of critical operations (`create_all`, `drop_all`, `clear_all`). This is a safety measure for the production environment.

-   Synchronous components

    -   `database_url` - Address for connecting to the synchronous database.
    -   `engine` - Mechanism for synchronous interaction with the database.
    -   `session` - Generator of synchronous sessions.
    -   `Base` - Base class for data models.
    -   Functionality:
        -   `get_session` - DB session injector.
        -   `get_session_transaction` - DB session injector with transaction support.
        -   `create_all` - Initialization of all tables in the database.
        -   `drop_all` - Deletion of the entire database structure.
        -   `clear_all` - Clearing the contents of tables. The `exclude_tables_name` parameter allows excluding certain tables from the clearing process.

-   Asynchronous components
    -   `adatabase_url` - Address for connecting to the asynchronous database.
    -   `aengine` - Asynchronous mechanism for working with the database, including connection pool.
    -   `asession` - Generator of asynchronous sessions.
    -   Functionality:
        -   `aget_session` - Asynchronous DB session injector.
        -   `aget_session_transaction` - Asynchronous DB session injector with transaction support.

### OrmAsync

This class optimizes asynchronous interaction with the database:

-   `get` - Retrieving an object based on given criteria.
-   `get_list` - Getting a set of objects by query. (With the possibility of deep selection)
-   `update` - Modifying objects according to the query.
-   `delete` - Deleting objects based on given parameters.
-   `get_item` - Retrieving an object by primary key. (With the possibility of deep selection)
-   `create_item` - Creating a new object. (With the possibility of cascade creation)
-   `update_item` - Updating an object by primary key. (With the possibility of cascade update)
-   `delete_item` - Deleting an object by primary key. (With the possibility of cascade deletion)

> Deep selection/cascade operations - the ability to work with related data.
> Activated by the `deep=True` parameter
> Examples:
>
> -   get_list, get_item - Return objects with all related data, ready for use in Pydantic
> -   create_item - Creates records in related tables
> -   update_item - Updates data in related tables
> -   delete_item - Deletes records from related tables

### ViewSet

ViewSet allows quickly creating CRUD operations for models. Here's an example of usage:

```python
from fastapi_accelerator.viewset import AppOrm, FullViewSet
from fastapi import APIRouter, Depends, Query
from app.api.v1.schemas.timemeasurement import TaskExecution
from app.models.timemeasurement import TaskExecution as TaskExecutionDb

router = APIRouter(prefix="/api/v1")

class FileViewSet(FullViewSet):
    """
    View for working with files
    """
    # DB Model
    db_model = TaskExecutionDb
    # Schema Model
    pydantic_model = TaskExecution

    '''
    # Caching
    cache_class = redis_client
    cache_ttl = timedelta(minutes=10)

    # Pagination
    paginator_class = DefaultPaginator

    # Enable support for nested pydantic schemas
    # this means that recursive creation, updating, deletion of related records will occur
    deep_schema = True

    # Enable protection through JWT
    dependencies = [Depends(jwt_auth)]

    # You can also override methods:
    async def db_update(
        self, item_id: str | int | UUID, item: type[BaseModel], aorm: OrmAsync
    ) -> object:
        """Overriding the db_update method"""
        return await super().db_update(item_id, item, aorm)

    def list(self):
        """Overriding the list method"""
        @self.router.get(f"{self.prefix}", tags=self.tags)
        async def get_list_items(
            skip: int = Query(0),
            limit: int = Query(100),
            aorm: OrmAsync = Depends(AppOrm.aget_orm),
        ) -> List[self.pydantic_model]:
            return await aorm.get_list(
                select(self.db_model).offset(skip).limit(limit),
                deep=self.deep_schema,
                db_model=self.db_model,
            )
        return get_list_items
    '''

router.views = [
    FileViewSet().as_view(router, prefix="/file"),
]
```

### JWT Authentication

We use JWT authentication to protect API endpoints:

```python
from fastapi_accelerator.auth_jwt import BaseAuthJWT

class AuthJWT(BaseAuthJWT):
    async def check_auth(username: str, password: str) -> bool:
        """Check the entered login and password."""
        return username == "admin" and password == "admin"

AuthJWT.mount_auth(app)
```

Example of protecting an API method:

```python
from fastapi_accelerator.auth_jwt import jwt_auth

@app.get("/check_protected", summary="Check JWT authentication")
async def protected_route(jwt: dict = Depends(jwt_auth)):
    return {"message": "This is a protected route", "user": jwt}
```

### Integrations with External APIs

Most API services interact with other APIs or gRPC/RPC services. Such integrations can be complex and often not fully understood by developers. Because of this, they easily turn into legacy code that is difficult to maintain, and testing integrations locally is often impossible.

It's important to have a library in the project that monitors the quality of integration writing and forces documentation to simplify further support. That's why I developed special modules:

-   `IntegrationHTTP`: Class for creating REST HTTP integrations.
-   `Stability Patterns`: Stability patterns to apply to integration methods.
-   `py2dantic`: Utility for converting Python dict to Pydantic schema.
-   `docintegration`: Auto-generation of documentation for used integrations.

Advantages of using this approach:

-   Explicit specification of request and response formats.
-   Easy portability of code between projects — just import classes based on `IntegrationHTTP`.
-   Consolidation of external request logic in one place, which simplifies maintenance.
-   Ability to easily replace real methods with `mock` for testing.
-   Easy implementation of `Stability Patterns` for integration methods.

To create an integration, follow these steps:

1. It's recommended to place integration code in the `app/integration/IntegrationPackageName` directory.

2. Create an integration class `app/integration/IntegrationPackageName/endpoint.py`:

```python
import httpx
from pydantic import BaseModel
from fastapi_accelerator.integration.http_integration import (
    ApiHTTP, EndpointsDeclaration, HTTPMethod, IntegrationHTTP,
)
from fastapi_accelerator.integration.stability_patterns import sp

class NameIntegration(EndpointsDeclaration):
    integration = IntegrationHTTP(
        "Integration Name",
        doc="Integration with ... API",
    )

    class Schema:
        """Pydantic schemas for successful responses"""
        class Successful(BaseModel):
            body: str

    class SchemaError:
        """Pydantic schemas for unsuccessful responses"""
        class http400(BaseModel):
            error: str

    @integration.endpoint(
        HTTPMethod.post,
        "/path",
        version="...",
        docurl="https://..."
    )
    @sp.RetryPattern()
    async def method_name(api: ApiHTTP, argument_1: str) -> Schema.Successful | SchemaError.http400:
        try:
            response: httpx.Response = await api.client.post(api.url.geturl(), json=...)
            return response.json()
        except httpx.RequestError as e:
            raise e
```

3. Configure and connect integrations to the project `app/core/useintegration.py`:

```python
"""Integrations used in the project"""
from app.integration.IntegrationPackageName.endpoint import NameIntegration

# Creating an instance of the integration
name_api = NameIntegration(
    # Beginning for url path
    base_url="https://path...",
    # Credentials that we can use in integration methods
    credentials={...},
)
```

4. Example of using the integration class in `FastAPI`:

```python
from app.core.useintegration import name_api
from app.integration.IntegrationPackageName.schema import NameSchema

@router.get("/name")
async def name(argument_1: str) -> NameIntegration.Schema.Successful:
    # Call the integration method
    return await name_api.method_name(argument_1)
```

## Testing

One of the key features of our toolkit is a powerful system for writing and executing tests. It includes:

1. Fixtures for working with a test database and API client.
2. Decorators for authentication and applying fixtures.
3. Context manager for tracking SQL queries.
4. Utilities for checking JSON responses.
5. Testing through classes.

Example of a test function:

```python
from typing import Callable, NamedTuple
from fastapi.testclient import TestClient
from app.fixture.items_v1 import export_fixture_file
from fastapi_accelerator.db.dbsession import MainDatabaseManager
from fastapi_accelerator.testutils import apply_fixture_db, client_auth_jwt, track_queries, check_response_json

# Authenticate test client
@client_auth_jwt(username="test")
# Create test data from function with fixtures
@apply_fixture_db(export_fixture_file)
def test_name(
    client: TestClient,  # Test client for API requests
    url_path_for: Callable,  # Function to get url by handler function name
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
```

Example of a test class:

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
    # Create test data from function with fixtures
    @apply_fixture_db(export_fixture_file)
    def setUp(self, fixtures: NamedTuple):
        self.url = BASE_URL_V1 + "taskexecution"
        self.fixtures = fixtures  # Stores created data from fixtures

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
```

## Comparison with Existing Solutions

While there are several projects offering tools for developing and testing FastAPI applications, our solution stands out for its comprehensiveness and specialization:

1. `FastAPI-Utils`: Provides utilities for development but is less focused on testing.
2. `FastAPI-SQLAlchemy`: Integrates FastAPI with SQLAlchemy, including some testing utilities.
3. `FastAPI-Toolkit`: Offers a set of tools but is less specialized in testing tasks.
4. `freddie` - Archived on GitHub, only provides viewset functionality.
5. `fastapi_viewsets` - Only offers viewset functionality.
6. `FastAPIwee` - Less specialized in testing tasks.

Our solution differs in that it:

1. Is more specific to FastAPI application testing tasks.
2. Provides a wider range of tools for various aspects of testing.
3. Includes unique features such as the `@apply_fixture_db` decorator and `track_queries` context manager.
4. Offers a comprehensive approach covering various aspects of FastAPI application development and testing.

## Conclusion

The presented toolkit significantly simplifies and accelerates development with FastAPI. It provides ready-made solutions for typical tasks, improves project structure, and facilitates testing. Using these tools will allow developers to focus on the business logic of the application rather than on technical implementation details.

Despite the presence of other tools in the FastAPI ecosystem, our solution stands out for its completeness and specialization in testing tasks. This makes it a valuable addition to existing resources for FastAPI developers.

We continue to develop this toolkit and welcome feedback from the community. If you have ideas for improvement or have found a bug, please create an issue in our GitHub repository.

By providing this comprehensive set of tools, we aim to contribute to the FastAPI community and help developers create more robust and efficient applications. The combination of powerful development utilities and advanced testing capabilities makes FastAPI Accelerator a valuable asset for both individual developers and teams working on FastAPI projects of any scale.

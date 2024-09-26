## Use Base Pattern

The `base_pattern` function adds many useful features to the `app`, including:

-   Populating `state` and other information for the `app`.
-   Enabling `CORS`.
-   Connecting routers with `ViewSet` support.
-   Adding a `healthcheck` method.
-   `Middleware` for debugging API request execution time.
-   Detailed output for `HTTP` exceptions.
-   Adding [docintegration](#use-docintegration)

## Use DatabaseManager

`DatabaseManager` is a universal tool for working with RDBMS, providing both synchronous and asynchronous (names starting with `a`) methods. `DatabaseManager` uses the singleton pattern, so it can be easily substituted in tests.

Example of creating a DB manager in the `app/db/base.py` file:

```python
"""Module for connecting to RDBMS"""

from app.core.config import DATABASE_URL, DEBUG, DEV_STATUS
from fastapi_accelerator.dbsession import MainDatabaseManager

# Manager for RDBMS
DatabaseManager = MainDatabaseManager(DATABASE_URL, echo=DEBUG, DEV_STATUS=DEV_STATUS)
```

### Main components of `MainDatabaseManager`

-   General characteristics

    -   `DEV_STATUS` - Development mode indicator. When `DEV_STATUS=False`, it blocks the execution of critical operations (`create_all`, `drop_all`, `clear_all`). This is a safety measure for the production environment.

-   Synchronous components

    -   `database_url` - Address for connecting to the synchronous database.
    -   `engine` - Mechanism for synchronous interaction with the DB.
    -   `session` - Generator of synchronous sessions.
    -   `Base` - Base class for data models.

    -   Functionality:

        -   `get_session` - DB session injector.
        -   `get_session_transaction` - DB session injector with transaction support.
        -   `create_all` - Initialization of all tables in the DB.
        -   `drop_all` - Deletion of the entire DB structure.
        -   `clear_all` - Clearing the contents of tables. The `exclude_tables_name` parameter allows excluding certain tables from the clearing process.

-   Asynchronous components

    -   `adatabase_url` - Address for connecting to the asynchronous DB.
    -   `aengine` - Asynchronous mechanism for working with the DB, including connection pool.
    -   `asession` - Generator of asynchronous sessions.

    -   Functionality:

        -   `aget_session` - Asynchronous DB session injector.
        -   `aget_session_transaction` - Asynchronous DB session injector with transaction support.

### Use OrmAsync

This class optimizes asynchronous interaction with the DB:

-   `get` - Retrieving an object based on given criteria.
-   `get_list` - Getting a set of objects based on a query. (With the possibility of deep selection)
-   `update` - Modifying objects according to a query.
-   `delete` - Deleting objects based on given parameters.
-   `get_item` - Retrieving an object by primary key. (With the possibility of deep selection)
-   `create_item` - Creating a new object. (With the possibility of cascade creation)
-   `update_item` - Updating an object by primary key. (With the possibility of cascade update)
-   `delete_item` - Deleting an object by primary key. (With the possibility of cascade deletion)
-   `eager_refresh` - Full loading of all related data for an object.

> Deep selection/cascade operations - the ability to work with related data.
> Activated by the `deep=True` parameter
>
> Examples:
>
> -   get_list, get_item - Return objects with all related data, ready for use in Pydantic
> -   create_item - Creates records in related tables
> -   update_item - Updates data in related tables
> -   delete_item - Deletes records from related tables

### Create a model using DatabaseManager

```python
from sqlalchemy import Column, Integer, String

from app.db.base import DatabaseManager


class User(DatabaseManager.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    login = Column(String, index=True)
    pthone = Column(String, index=True)
    email = Column(String, unique=True, index=True)
```

### Performing CRUD through DatabaseManager

```python
# Asynchronous version
class FileView:
    @router.get("/file")
    async def get_files(
        skip=Query(0),
        limit=Query(100),
        aorm: OrmAsync = Depends(DatabaseManager.aget_orm),
    ) -> List[File]:
        return await aorm.get_list(select(FileDb).offset(skip).limit(limit))

    @router.get("/file/{file_uid}")
    async def get_file(
        file_uid: str = Path(),
        aorm: OrmAsync = Depends(DatabaseManager.aget_orm),
    ) -> File:
        return await aorm.get(select(FileDb).filter(FileDb.uid == file_uid))

    @router.post("/file")
    async def create_file(
        aorm: OrmAsync = Depends(DatabaseManager.aget_orm),
    ) -> File:
        file_uid = uuid.uuid4()
        new_user = FileDb(uid=file_uid)
        return await aorm.create_item(new_user)

    @router.put("/file/{file_uid}")
    async def update_file(
        file_uid: str = Path(),
        aorm: OrmAsync = Depends(DatabaseManager.aget_orm),
    ) -> File:
        update_data = {"filename": "new"}
        return await aorm.update(
            update(FileDb).filter(FileDb.uid == file_uid), update_data
        )

    @router.delete("/file/{file_uid}")
    async def delte_file(
        file_uid: str = Path(),
        aorm: OrmAsync = Depends(DatabaseManager.aget_orm),
    ):
        return await aorm.delete(delete(FileDb).filter(FileDb.uid == file_uid))

# Synchronous version
@router.get("/file-sync")
async def get_file_sync(
    session: Session = Depends(DatabaseManager.get_session),
) -> List[File]:
    skip = 0
    limit = 100
    res = session.query(FileDb).offset(skip).limit(limit).all()
    return res
```

### Working with migrations through Alembic

1.  Installation

```bash
poetry add alembic
```

2.  Project initialization

```bash
alembic init alembic
```

3.  Modify `alembic/env.py`

```python
# Import the DB manager
from app.core.db import DatabaseManager

# > ! Import models that need to be tracked
from app.models import *  # noqa F401

from fastapi_accelerator.pattern.pattern_alembic import AlembicEnv

# Pre-configured logic for creating and executing migrations through Alembic
AlembicEnv(DatabaseManager).run()
```

4. We can modify `alembic.ini`

```ini
# Format for the migration file name
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
```

> Important aspect of migration search
>
> Models need to be imported in `alembic/env.py` so that these models record their data in `Base.metadata`
>
> Therefore, you need to:
>
> 1. In `app.models.__init__.py` import all models
>
> ```python
> from .files import *
> from .users import *
> ```
>
> 2. In `alembic/env.py` import all (or only specific) models
>
> ```python
> from app.models import *
> ```

5. Create migrations and apply them

```bash
# Create a migration
alembic revision --autogenerate
# Apply migration to the DB
alembic upgrade head
```

## Use Cache

-   Preliminary setup, fill in the `app/core/cache.py` file:

```python
import redis.asyncio as redis

from app.core.config import REDIS_URL

# Create a global Redis object
redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
```

-   You can use API response caching through the `@cache_redis()` decorator

```python
from datetime import timedelta
from fastapi_accelerator.cache import cache_redis

@app.get(f"files/{{item_id}}")
@cache_redis(cache_class=redis_client, cache_ttl=timedelta(minutes=10))
async def get_item(
    request: Request,
    item_uid: str = Path(...),
    aorm: OrmAsync = Depends(DatabaseManager.aget_orm),
) -> FilesSchema:
    response = await aorm.get(
        select(Files).filter(Files.id == item_uid)
    )
    return response
```

## Use ViewSet

1. Let's create, for example, `app/api/v1/router.py`

```python
from datetime import timedelta
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.file import File
from app.api.v1.schemas.timemeasurement import TaskExecution
from app.api.v1.schemas.user import User
from app.core.cache import redis_client
from app.core.db import DatabaseManager
from app.models.file import File as FileDb
from app.models.timemeasurement import TaskExecution as TaskExecutionDb
from app.models.users import User as UserDb
from fastapi_accelerator.auth_jwt import jwt_auth
from fastapi_accelerator.db.dbsession import OrmAsync
from fastapi_accelerator.paginator import DefaultPaginator
from fastapi_accelerator.viewset import AppOrm, FullViewSet

router = APIRouter(prefix="/api/v1")

class FileViewSet(FullViewSet):
    """
    View for working with files
    """

    # DB Model
    db_model = FileDb
    # Schema Model
    pydantic_model = File
    # Caching
    cache_class = redis_client
    cache_ttl = timedelta(minutes=10)
    # Pagination
    paginator_class = DefaultPaginator

    async def db_update(
        self, item_id: str | int | UUID, item: type[BaseModel], aorm: OrmAsync
    ) -> object:
        """Overriding the db_update method"""
        return await super().db_update(item_id, item, aorm)


class UserViewSet(FullViewSet):
    """
    View for working with users
    """

    # DB Model
    db_model = UserDb
    # Schema Model
    pydantic_model = User

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

class TaskExecutionViewSet(FullViewSet):
    """
    View for working with task executions
    """

    # DB Model
    db_model = TaskExecutionDb
    # Schema Model
    pydantic_model = TaskExecution

    # Pagination
    paginator_class = DefaultPaginator

    # Enable support for nested pydantic schemas
    # this means that recursive creation, updating,
    # and deletion of related records will occur
    deep_schema = True

    # Enable protection through JWT
    dependencies = [Depends(jwt_auth)]

# Connect ViewSet
router.views = [
    FileViewSet().as_view(router, prefix="/file"),
    UserViewSet().as_view(router, prefix="/user"),
    TaskExecutionViewSet().as_view(router, prefix="/taskexecution"),
]
```

## Use Time Zone

Get the current server time considering its time zone

```python
import pytz
from fastapi_accelerator.timezone import get_datetime_now

# Option 1
get_datetime_now(request.app.state.TIMEZONE).isoformat()
# Option 2
get_datetime_now(app.state.TIMEZONE).isoformat()
# Option 3
get_datetime_now(pytz.timezone("Europe/Moscow")).isoformat()
# Option 4
timezone = TIMEZONE() or TIMEZONE(request.app)
get_datetime_now(timezone).isoformat()
```

## Use HTTPException

-   Usage:

```python
from fastapi_accelerator.exception import HTTPException403

@router.get("/")
async def get_users():
    if True:
        raise HTTPException403()
    return [{"user_id": "user1"}, {"user_id": "user2"}]
```

## Use AuthJWT

Using authentication through JWT

-   Connect to FastAPI project:

```python
from fastapi_accelerator.auth_jwt import BaseAuthJWT

class AuthJWT(BaseAuthJWT):
    async def check_auth(username: str, password: str) -> bool:
        """Check the entered login and password."""
        return username == "admin" and password == "admin"

    async def add_jwt_body(username: str) -> dict:
        """Function to add additional data to the user's JWT token"""
        return {"version": username.title()}


# Connect JWT authentication
AuthJWT.mount_auth(app)
```

-   Example of protecting an API method:

```python
from fastapi_accelerator.auth_jwt import jwt_auth

@app.get("/check_protected", summary="Check JWT authentication")
async def protected_route(jwt: dict = Depends(jwt_auth)):
    return {"message": "This is a protected route", "user": jwt}
```

Here's the translation of the text into English while preserving its structure:

## Use Integration

Most API services interact with other APIs or gRPC/RPC services. Such integrations can be complex and often not fully understood by developers. Because of this, they easily turn into legacy code that is difficult to maintain, and testing integrations locally is often impossible.

It's important to have a library in the project that monitors the quality of integration writing and forces documentation to simplify further support. For this purpose, I developed special modules:

-   `IntegrationHTTP`: A class for creating HTTP integrations.

-   `Stability Patterns`: Stability patterns to apply to integration methods.

-   `py2dantic`: A utility for converting Python dict to Pydantic schema.

-   `docintegration`: Auto-generation of documentation for used integrations.

### Use Integration HTTP

`IntegrationHTTP` - A class for creating HTTP integration methods, centralizing the logic of calls to external systems, validating outgoing data. The class also specifies the version and documentation of the external API.

Advantages of using this approach:

-   Explicit specification of request and response formats.

-   Easy portability of code between projects — just import classes based on `IntegrationHTTP`.

-   Consolidation of external request logic in one place, simplifying maintenance.

-   Ability to easily replace real methods with `mock` for testing.

-   Easy implementation of `Stability Patterns` for integration methods.

To create an integration, follow these steps:

1. It is recommended to place integration code in the directory `app/integration/IntegrationPackageName`.

2. Create an integration class `app/integration/IntegrationPackageName/endpoint.py`:

```python
import httpx
from pydantic import BaseModel
from fastapi_accelerator.integration.http_integration import (
    ApiHTTP,
    EndpointsDeclaration,
    HTTPMethod,
    IntegrationHTTP,
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

# Creating an instance of integration
name_api = NameIntegration(
    # Start for url path
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
    # Call integration method
    return await name_api.method_name(argument_1)
```

---

You need to specify the type of object returned from the integration method.

The response can be:

-   `dict`: which can be converted to a single `Pydantic` schema.

-   `list[dict]`: which can be converted to a list of `Pydantic` schemas.

-   Multiple response types: This is necessary to specify the type of correct response and for error handling. For example, `-> SuccessfulResponse | UnsuccessfulResponse` or `-> list[SuccessfulResponse] | UnsuccessfulResponse`.

-   In the worst case, you can specify `Any`.

#### Example of integration with Google Translate

-   Integration class `app/integration/google_translate/endpoint.py`:

```python
import httpx
from pydantic import BaseModel
from fastapi_accelerator.integration.http_integration import (
    ApiHTTP,
    EndpointsDeclaration,
    HTTPMethod,
    IntegrationHTTP,
)
from fastapi_accelerator.integration.stability_patterns import sp

class GoogleTranslateEndpoints(EndpointsDeclaration):
    integration = IntegrationHTTP(
        "Google Translate",
        doc="Integration with Google Translate API",
    )

    class Schema:
        """Schemas for successful responses"""
        class TranslateV2(BaseModel):
            text: str

    class SchemaError:
        """Schemas for unsuccessful responses"""
        class http400Error(BaseModel):
            code: int
            message: str
            errors: list[dict]
            status: str
            details: list[dict]

        class http400(BaseModel):
            error: dict

    @integration.endpoint(
        HTTPMethod.post,
        "/v1/translateHtml",
        version="v2",
        docurl="https://cloud.google.com/translate/docs/reference/rest",
    )
    # Apply stability patterns
    @sp.Timeout()
    # Automatically retries the request when an error occurs.
    @sp.RetryPattern()
    async def translate(
        api: ApiHTTP,
        text: str,
        from_lang: str,
        to_lang: str,
    ) -> Schema.TranslateV2 | SchemaError.http400: # Specify response type
        """Translate text using Google Translate"""
        try:
            # Execute request to external system
            response: httpx.Response = await api.client.post(
                api.url.geturl(),
                json=[[text.split("\n"), from_lang, to_lang], "te_lib"],
                headers={
                    "content-type": "application/json+protobuf",
                    "x-goog-api-key": api.credentials["API_TOKEN"],
                },
            )
            # Process response
            print(f"Processed {api.url}: Status {response.status_code}")
            return {"text": "\n".join(x[0] for x in response.json())}
        except httpx.RequestError as e:
            print(f"Error processing {api.url}: {e}")
            raise e
```

-   Connection in `app/core/useintegration.py`:

```python
"""Integrations used in the project"""
from app.integration.google_translate.endpoint import GoogleTranslateIntegration

# Creating an instance of integration
gtapi = GoogleTranslateIntegration(
    base_url="https://translate-pa.googleapis.com",
    # Save credentials in the class that we can use in integration methods
    credentials={"API_TOKEN": "..."},
)
```

-   Example of usage in a `FastAPI` endpoint:

```python
from datetime import timedelta
from fastapi_accelerator.cache import cache_redis
from app.core.cache import redis_client
from app.core.useintegration import gtapi
from app.integration.google_translate.schema import GoogleTranslateSchema

@router.get("/translate")
# We can easily cache responses from integrations
@cache_redis(cache_class=redis_client, cache_ttl=timedelta(minutes=10))
async def translate(
    text: str, from_lang: str = "en", to_lang: str = "ru"
) -> GoogleTranslateEndpoints.Schema.TranslateV2:
    # Call integration method
    return await gtapi.translate(text, from_lang, to_lang)
```

### Use Stability Patterns

The module supports stability patterns that help avoid errors and overloads when working with external services.

> The main criterion for unsuccessful execution is the occurrence of an exception (raise) in the integration method. If you received a response with code 400 (client error) or 500 (server error), but did not raise an exception, Stability Patterns will consider this a successful execution and will not apply its error handling logic.

Below is a description of the main decorators:

-   `@sp.Fallback` (Fallback) - Provides an alternative execution path in case of main path failure. Allows the system to degrade in a controlled manner rather than failing with an error.
-   `@sp.Timeout` (Timeout) - Limits the response waiting time from an external service. Prevents resource blocking when a call hangs.
-   `@sp.CircuitBreaker` (Circuit Breaker) - Tracks the number of errors when calling an external service. When the limit is exceeded, it temporarily blocks the call, preventing cascading failures.
-   `@sp.RetryPattern` (Retry Pattern) - Automatically retries the request when an error occurs.
-   `@sp.Throttling` (Throttling) - Limits the number of requests to a resource to prevent its overload. Protects the system from request storms.

These patterns make the system more resilient, minimizing the risk of failures and ensuring smooth degradation when problems occur.

Вот перевод оставшейся части текста на английский язык с сохранением структуры:

### Use docintegration

This functionality allows you to find out which integrations are used in the project, similar to how it's implemented in OpenAPI Swagger for standard FastAPI.

The documentation is available at: `http://host:port/docintegration`.

To activate this path, you need to specify a list of integrations in the `useintegration` argument of the `base_pattern` parameter in the `main.py` file:

```python
from app.core.useintegration import integration_1, integration_2
from fastapi_accelerator.pattern.pattern_fastapi import base_pattern

# Pattern for the project
base_pattern(
    app,
    ...,
    useintegration=[integration_1, integration_2],
)
```

Documentation appearance

## Use Admin Panel

1. Installation

```bash
poetry add flask-admin
```

2. Create a file `admin_panel.py`

```python
from flask import Flask

from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME, SECRET_KEY
from app.db.base import DatabaseManager
from app.models import File, User
from fastapi_accelerator.pattern_flask_admin import base_pattern

app = Flask(__name__)

admin = base_pattern(
    app,
    SECRET_KEY,
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    # > Models needed in the admin panel
    models=[User, File],
    database_manager=DatabaseManager,
)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8001,
        debug=True,
    )
```

3. Run `python admin_panel.py`

4. Log in to the admin panel:

-   `http://localhost:8233/admin`
-   `http://localhost:8233/login`
-   `http://localhost:8233/logout`

## Description of files in the fastapi_accelerator package

```bash
fastapi_accelerator/

├── db/ # Logic for interacting with RDBMS
│ ├── __init__.py
│ ├── dborm.py
│ └── dbsession.py
│
├── pattern/ # Templates for projects
│ ├── __init__.py
│ ├── pattern_fastapi.py # Templates for creating a FastAPI project
│ ├── pattern_alembic.py # Templates for creating Alembic
│ └── pattern_flask_admin.py # Templates for creating a Flask admin panel project
│
├── integration/ # Utilities for integrations with external systems
│ ├── __init__.py
│ ├── base_integration.py # Base class for all types of integrations
│ ├── http_integration.py # HTTP integrations
│ └── stability_patterns.py # Implementation of stability patterns
│
├── commands/ # CLI commands
│ ├── __init__.py
│ └── py2dantic # Generating pydantic schema from python dict
│
├── testutils # Utilities for testing FastAPI
│ ├── __init__.py
│ ├── fixture_base.py # Main fixture for tests
│ ├── fixture_db # Fixtures for working with test DB
│ │ ├── __init__.py
│ │ ├── apply_fixture.py
│ │ ├── db.py
│ │ └── trace_sql.py
│ ├── fixture_auth.py # Fixture for client authentication via JWT
│ └── utils.py
│
├── cache.py # Caching implementation
├── auth_jwt.py # JWT authentication
├── exception.py # Exception handling
├── middleware.py # Middleware components
├── paginator.py # Pagination implementation
├── timezone.py # Working with time zones
├── appstate.py # Get project settings once during Runtime
├── viewset.py # ViewSet implementation
├── utils.py # General utilities
├── README.md # Documentation
└── __init__.py
```

## File examples

### Example of `main.py`

```python
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import app.api.v1.router as RouterV1
from app.core.config import BASE_DIR_PROJECT, DEBUG, SECRET_KEY
from app.core.db import DatabaseManager
from app.core.security import AuthJWT
from fastapi_accelerator.pattern_fastapi import base_pattern
from fastapi_accelerator.timezone import moscow_tz

@asynccontextmanager
async def lifespan(app):
    """Project lifecycle"""
    yield

app = FastAPI(
    title="File ddos API",
    # Lifespan function
    lifespan=lifespan,
    # Dependencies that will be applied to all routes in this router.
    dependencies=None,
    # Default response class for all routes.
    default_response_class=ORJSONResponse,

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
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        reload=DEBUG,
        access_log=DEBUG,
```

Run with `python main.py`

### Example of `Makefile`

```makefile
run_test:
    pytest

run_dev_server:
    python -m main

# Create migration
makemigrate:
    alembic revision --autogenerate

# Apply migrations
migrate:
    alembic upgrade head
```

### Example of `config.py`

File `app/core/config.py`:

```python
"""
Global project settings.
Can additionally contain conversion of setting values from `.settings_local`
"""

from pathlib import Path
from .settings_local import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    CACHE_STATUS,
    DATABASE_URL,
    DEBUG,
    DEV_STATUS,
    REDIS_URL,
    SECRET_KEY,
    TEST_DATABASE_URL,
)

# Path to the project application
BASE_DIR_APP = Path(__file__).parent.parent
# Path to the project root
BASE_DIR_PROJECT = BASE_DIR_APP.parent

__all__ = (
    # >>> Connections to external systems:
    # URL for connecting to the DB
    DATABASE_URL,
    # URL for connecting to the test DB
    TEST_DATABASE_URL,
    # URL for connecting to Redis
    REDIS_URL,
    # >>> Statuses:
    # Debug mode, can be enabled on the test server
    DEBUG,
    # Development mode, enable only in local development
    DEV_STATUS,
    # Enable/Disable caching
    CACHE_STATUS,
    # >>> Security:
    SECRET_KEY,
    # Login data for Flask-Admin panel
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
)
```

File `app/core/settings_local.py`:

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://user_app:db@postgres_db:5432/db")
TEST_DATABASE_URL = "postgres://user_app:db@postgres_db:5432/testdb"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
SECRET_KEY = "your_secret_key_here"
DEBUG = True
DEV_STATUS = False
CACHE_STATUS = True
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"
```

### Example of file structure

```bash
Project/
│
├── app/
│ ├── __init__.py
│ ├── utils.py # Reusable functionality for the project
│ ├── core/ # Contains core modules such as configuration, security, and common dependencies.
│ │ ├── __init__.py
│ │ ├── settings_local.py # Local values for settings, should not be in git, create directly on the server
│ │ ├── config.py # Project settings that do not depend on external settings
│ │ ├── security.py # Project security logic
│ │ ├── db.py # Database settings and sessions.
│ │ ├── cache.py # Caching settings
│ │ ├── useintegration.py # Integrations used in the project
│ │ └── dependencies.py # Common dependencies for the project
│ │
│ ├── api/ # Contains all API endpoints, divided by versions.
│ │ ├── __init__.py
│ │ └── v1/
│ │ ├── __init__.py
│ │ ├── router.py # Contains request handlers for the specified api version
│ │ │
│ │ ├── static/ # Contains static files, if needed
│ │ │ ├── js
│ │ │ ├── css
│ │ │ ├── img
│ │ │ └── html
│ │ │
│ │ ├── logic/ # Contains business logic
│ │ │ ├── __init__.py
│ │ │ ├── users.py
│ │ │ └── items.py
│ │ │
│ │ ├── schemas/ # Pydantic models for request and response validation.
│ │ │ ├── __init__.py
│ │ │ ├── user.py
│ │ │ └── item.py
│ │ │
│ │ ├── crud/ # Functions for working with the database (Create, Read, Update, Delete).
│ │ │ ├── __init__.py
│ │ │ ├── user.py
│ │ │ └── item.py
│ │ │
│ │ └── tests/ # Directory for tests.
│ │ ├── __init__.py
│ │ ├── test_users.py
│ │ └── test_items.py
│ │
│ ├── models/ # Database model definitions (e.g., SQLAlchemy models).
│ │ ├── __init__.py
│ │ ├── user.py
│ │ └── item.py
│ │
│ ├── integration/ # Integrations with external services
│ │ ├── __init__.py
│ │ ├── google_translate/ # Example of integration package with Google Translator (it can be connected as a git submodule)
│ │ │    └── __init__.py
│ │ ├── schema.py # Contains request and response schemas
│ │ └── view.py # Contains integration logic
│ │
│ └── fixture/ # Stores fixtures for testing this project
│ ├── __init__.py
│ ├── items_v1.py # Test records for DB
│ └── utils.py # Reusable fixtures for tests
│
├── fastapi_accelerator/ # Submodule for reuse
│
├── alembic/ # Directory for database migrations.
│ ├── versions/ # Folder with migrations
│ │ ├── __init__.py
│ │ └── 0001_init.py # Migration file
│ └── env.py # Settings for alembic
│
├─ conf/ # Configuration files for prod
│ ├── settings_local.example.py # Example for creating settings_local.py
│ └── Dockerfile # File for prod
│
├── pytest.ini # Configuration for pytest
├── conftest.py # Test execution settings
│
├── .gitignore # Which files and folders to ignore in git
├── .gitlab-ci.yml # CI pipeline settings
│
├── pyproject.toml # Poetry settings
│
├── Makefile # Reusable bash commands
│
├── README.md # Project description
├── CHANGELOG.md # Project changes
├── version.toml # Project version
│
├── alembic.ini # Configurations for alembic
│
├── DockerfileDev # File for creating dev container with APP
├── docker-compose.yml # Used for building dev environment
│
├── admin_panel.py # Admin panel
│
└── main.py # Entry point to the application, where the FastAPI instance is created.
```

![Test](https://github.com/eadwinCode/django-ninja-extra/workflows/Test/badge.svg)
[![PyPI version](https://badge.fury.io/py/django-ninja-extra.svg)](https://badge.fury.io/py/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/v/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/pyversions/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/djversions/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![Codecov](https://img.shields.io/codecov/c/gh/eadwinCode/django-ninja-extra)](https://codecov.io/gh/eadwinCode/django-ninja-extra)
[![Downloads](https://static.pepy.tech/badge/django-ninja-extra)](https://pepy.tech/project/django-ninja-extra)

# Django Ninja Extra

**Django Ninja Extra** package offers a **class-based** approach plus extra functionalities that will speed up your RESTful API development with [**Django Ninja**](https://django-ninja.rest-framework.com)

**Key features:**

All **Django-Ninja** features :
- **Easy**: Designed to be easy to use and intuitive.
- **FAST execution**: Very high performance thanks to **<a href="https://pydantic-docs.helpmanual.io" target="_blank">Pydantic</a>** and **<a href="/async-support/">async support</a>**.
- **Fast to code**: Type hints and automatic docs lets you focus only on business logic.
- **Standards-based**: Based on the open standards for APIs: **OpenAPI** (previously known as Swagger) and **JSON Schema**.
- **Django friendly**: (obviously) has good integration with the Django core and ORM.

Plus **Extra**:
- **Class Based**: Design your APIs in a class based fashion.
- **Permissions**: Protect endpoint(s) at ease with defined permissions and authorizations at route level or controller level.
- **Dependency Injection**: Controller classes supports dependency injection with python [**Injector** ](https://injector.readthedocs.io/en/latest/) or [**django_injector**](https://github.com/blubber/django_injector). Giving you the ability to inject API dependable services to APIController class and utilizing them where needed

---

### Requirements
- Python >= 3.6
- django >= 2.1 
- pydantic >= 1.6 
- Django-Ninja >= 0.16.1

Full documentation, [visit](https://eadwincode.github.io/django-ninja-extra/).

## Installation

```
pip install django-ninja-extra
```
After installation, add `ninja_extra` to your `INSTALLED_APPS`

```Python 
INSTALLED_APPS = [
    ...,
    'ninja_extra',
]
```

## Usage

In your django project next to urls.py create new `api.py` file: 

```Python
from ninja_extra import NinjaExtraAPI, api_controller, http_get

api = NinjaExtraAPI()

# function based definition
@api.get("/add", tags=['Math'])
def add(request, a: int, b: int):
    return {"result": a + b}

#class based definition
@api_controller
class MathAPI:

    @http_get('/subtract',)
    def subtract(self, a: int, b: int):
        """Subtracts a from b"""
        return {"result": a - b}

    @http_get('/divide',)
    def divide(self, a: int, b: int):
        """Divides a by b"""
        return {"result": a / b}
    
    @http_get('/multiple',)
    def multiple(self, a: int, b: int):
        """Multiples a with b"""
        return {"result": a * b}
    
api.register_controllers(
    MathAPI
)
```

Now go to `urls.py` and add the following:

```Python
...
from django.urls import path
from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),  # <---------- !
]

```

### Interactive API docs

Now go to <a href="http://127.0.0.1:8000/api/docs" target="_blank">http://127.0.0.1:8000/api/docs</a>

You will see the automatic interactive API documentation (provided by <a href="https://github.com/swagger-api/swagger-ui" target="_blank">Swagger UI</a>):

![Swagger UI](docs/images/ui_swagger_preview_readme.gif)

## Tutorials
- [django-ninja - Permissions, Controllers & Throttling with django-ninja-extra!](https://www.youtube.com/watch?v=yQqig-c2dd4) - Learn how to use permissions, controllers and throttling with django-ninja-extra
- [BookStore API](https://github.com/eadwinCode/bookstoreapi) - A sample project that demonstrates how to use django-ninja-extra with ninja schema and ninja-jwt

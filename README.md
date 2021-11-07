![Test](https://github.com/eadwinCode/django-ninja-extra/workflows/Test/badge.svg)
[![PyPI version](https://badge.fury.io/py/django-ninja-extra.svg)](https://badge.fury.io/py/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/v/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/pyversions/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)
[![PyPI version](https://img.shields.io/pypi/djversions/django-ninja-extra.svg)](https://pypi.python.org/pypi/django-ninja-extra)

# Django Ninja Extra

**Django Ninja Extra** is a utility library built on top of **Django Ninja** for building and setting up APIs at incredible speed and performance. It adds **DRF** batteries to [**Django Ninja**](https://django-ninja.rest-framework.com) and they are really extensible for custom use-cases.

**Key features:**
All Django-Ninja features are fully supported plus others below:

- **Class Based**: Design your APIs in a class based fashion.
- **Route Permissions**: Protect endpoint(s) at ease with defined permissions. It could be specific to a route or general to all routes
- **Dependency Injection**: Controller classes supports dependency injection with python [**Injector** ](https://injector.readthedocs.io/en/latest/) or [**django_injector**](https://github.com/blubber/django_injector)

---
## Documentation
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
from ninja_extra import NinjaExtraAPI
from ninja_extra import APIController, route, router
from ninja_extra.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import UserProfile

api = NinjaExtraAPI()
user_model = get_user_model()

# function based definition
@api.get("/add", tags=['Math'])
def add(request, a: int, b: int):
    return {"result": a + b}

#class based definition
@router('/', tags=['Math'], permissions=[])
class MathAPI(APIController):

    @route.get('/subtract',)
    def subtract(self, a: int, b: int):
        """Subtracts a from b"""
        return {"result": a - b}

    @route.get('/divide',)
    def divide(self, a: int, b: int):
        """Divides a by b"""
        return {"result": a / b}
    
    @route.get('/multiple',)
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
from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),  # <---------- !
]
```

### Interactive API docs

Now go to <a href="http://127.0.0.1:8000/api/docs" target="_blank">http://127.0.0.1:8000/api/docs</a>

You will see the automatic interactive API documentation (provided by <a href="https://github.com/swagger-api/swagger-ui" target="_blank">Swagger UI</a>):

![Swagger UI](docs/docs/images/ui_swagger_preview_readme.gif)
## What next?
- To support this project, please give star it on Github

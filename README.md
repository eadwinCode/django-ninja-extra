# Django Ninja Extra

**Django Ninja Extra** is a utility library built on top of **Django Ninja** for building and setting up APIs at incredible speed and performance. It adds **DRF** batteries to [**Django Ninja**](https://django-ninja.rest-framework.com) which are really extensible for custom use-cases.

**Key features:**
All Django-Ninja features are fully supported plus others below:

- **Class Based**: Design your APIs in a class based fashion.
- **Route Permissions**: Protect endpoint(s) at ease, specific or general
- **Dependency Injection**: Controller classes supports dependency injection with python [**Injector** ](https://injector.readthedocs.io/en/latest/) and [**django_injector**](https://github.com/blubber/django_injector)

---

## Installation

```
pip install django-ninja-extra
```

## Usage

In your django project next to urls.py create new `api.py` file:

```Python
from ninja_extra import NinjaExtraAPI
from ninja_extra import APIController, route, router
from ninja_extra.permissions import AllowAny
from ninja_extra.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import UserProfile

api = NinjaExtraAPI()
user_model = get_user_model()

# function based definition
@api.get("/add")
def add(request, a: int, b: int):
    return {"result": a + b}

#class based definition
@router('/users', tags=['users'], permissions=[])
class UserController(APIController):

    @route.get('/{user_id}', response=UserSchema, permissions=[AllowAny])
    def get_user(self, user_id: int):
        """get user by id"""
        user = get_object_or_404(user_model, pk=user_id)
        response_object = UserSchema.from_django(user)
        return response_object

    @route.get(
        '/{user_id}/profile',
        response=UserProfileSchema,
        permissions=[AllowAny]
    )
    def get_user_profile(self, user_id: int):
        """gets a user's profile by user id"""
        user_profile = get_object_or_404(UserProfile, user_id=user_id)
        return user_profile


api.register_controllers(
    UserController
)
```

Now go to `urls.py` and add the following:

```Python hl_lines="3 7"
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

![Swagger UI](docs/docs/img/index-swagger-ui.png)

## What next?

- Full documentation here - Still in progress
- To support this project, please give star it on Github

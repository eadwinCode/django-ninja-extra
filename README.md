# Django Ninja Extra

**Django Ninja Extra** is a utility library built on top of **Django Ninja** for building and setting up APIs at incredible speed and performance. It adds **DRF** batteries to **Django Ninja** and they are really extensible for custom use-cases.

**Key features:**

- **Class Based**: Design your APIs in a class based fashion.
- **Async Model Fetch Support**: Supports Django's ORM current async solution
- **Route Permissions**: Protect endpoint(s) at ease, specific or general
- **Route Pagination**: Paginate route(s) with ease

---

## Installation

```
pip install django-ninja-extra
```

or

```
pip install git+https://github.com/eadwinCode/django-ninja-extra.git
```

## Usage

In your django project next to urls.py create new `api.py` file:

```Python
from ninja_extra import NinjaExtraAPI
from ninja_extra import APIController, route
from ninja_extra.permissions import AllowAny
from ninja_extra.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

api = NinjaExtraAPI()
user_model = get_user_model()

@api.get("/add")
def add(request, a: int, b: int):
    return {"result": a + b}


class UserController(APIController):
    prefix: '/users'

    @route.get('/{user_id}', response=UserSchema, permissions=[AllowAny])
    def get_user(self, context, user_id: int):
        """get user by id"""
        user = get_object_or_404(user_model, pk=user_id)
        response_object = UserSchema.from_django(user)
        return response_object

    @route.retrieve(
        '/{user_id}/profile',
        response=UserProfileSchema,
        permissions=[AllowAny],
        query_set=UserProfile.objects.all(),
        lookup_url_kwarg='user_id',
        lookup_field='user'
    )
    def get_user_profile(self, context, user_id: int):
        """gets a user's profile by user id"""
        return context.object


api.register_controllers(
    UserController,
    NewsController
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

**That's it !**

Now you've just created an API that:

- receives an HTTP GET request at `/api/add`
- takes, validates and type-casts GET parameters `a` and `b`
- decodes the result to JSON
- generates an OpenAPI schema for defined operation

### Interactive API docs

Now go to <a href="http://127.0.0.1:8000/api/docs" target="_blank">http://127.0.0.1:8000/api/docs</a>

You will see the automatic interactive API documentation (provided by <a href="https://github.com/swagger-api/swagger-ui" target="_blank">Swagger UI</a>):

![Swagger UI](docs/docs/img/index-swagger-ui.png)

## What next?

- Read the full documentation here - Still in progress
- To support this project, please give star it on Github
- Permission feature is not fully ready
- Unit Test is in progress

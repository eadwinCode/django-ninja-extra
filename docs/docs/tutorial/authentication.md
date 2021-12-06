# **Authentication**

**Django Ninja Extra** provides the same API for authorization and authentication as in **Django-Ninja**.

## **Automatic OpenAPI schema**

Here's an example where the client, in order to authenticate, needs to pass a header:

`Authorization: Bearer supersecret`

```Python
from ninja.security import HttpBearer
from ninja_extra import api_controller, route
from ninja.constants import NOT_SET


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token == "supersecret":
            return token

@api_controller(tags=['My Operations'], auth=NOT_SET, permissions=[])
class MyController:
    @route.get("/bearer", auth=AuthBearer())
    def bearer(self):
        return {"token": self.request.auth}

```

## **Global authentication** 

In case you need to secure **all** route methods defined in `api` and APIController, you can pass the `auth` argument to the `NinjaExtraAPI` constructor:


```Python
from ninja_extra import NinjaExtraAPI
from ninja.security import HttpBearer


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        if token == "supersecret":
            return token


api = NinjaExtraAPI(auth=GlobalAuth())

```
Read more on django-ninja [authentication](https://django-ninja.rest-framework.com/tutorial/authentication/)

## **JWT Authentication**
if you want to use JWT authentication. See [ninja-jwt](https://pypi.org/project/django-ninja-jwt/)
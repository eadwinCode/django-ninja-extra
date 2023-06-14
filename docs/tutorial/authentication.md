# **Authentication**

**Django Ninja Extra** offers the same API for authorization and authentication as in **Django Ninja**, ensuring consistency and ease of use across both packages.

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
        return {"token": self.context.request.auth}

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

## Asynchronous Auth Classes

Ninja Extra added Asynchronous support for all `Auth` base classes provided by Django Ninja in `ninja_extra.security` package.
And it maintained similar interface. It is important to noted that when using these asynchronous auth classes, the endpoint handler 
**must** asynchronous functions.

For example, lets re-write the first auth example with `AsyncHttpBearer` class.

```Python
from ninja_extra import api_controller, route
from ninja_extra.security import AsyncHttpBearer
from ninja.constants import NOT_SET


class AuthBearer(AsyncHttpBearer):
    async def authenticate(self, request, token):
        # await some actions
        if token == "supersecret":
            return token


@api_controller(tags=['My Operations'], auth=NOT_SET, permissions=[])
class MyController:
    @route.get("/bearer", auth=AuthBearer())
    async def bearer(self):
        return {"token": self.context.request.auth}

```
In example above, we changed `HttpBearer` to `AsyncHttpBearer` and changed bearer to `async` endpoint. 
If `AuthBearer` is to be applied to a `MyController` **auth**, then all route handlers under `MyController` must be asynchronous route handlers.


## **JWT Authentication**
if you want to use JWT authentication. See [ninja-jwt](https://pypi.org/project/django-ninja-jwt/)

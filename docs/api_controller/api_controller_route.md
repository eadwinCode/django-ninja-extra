# **APIController Route Decorator**

The `route` class is a function decorator, used to mark an instance function of an APIController class, as an endpoint.

!!! info
    `ControllerRoute` or `route` is not the same with **django-ninja** `router` and can't be used interchangeably.

For example
```python
from ninja_extra import route, api_controller
from ninja_extra.controllers import RouteFunction

@api_controller
class MyController:
    @route.get('/test')
    def test(self):
        return {'message': 'test'}

assert isinstance(MyController.test, RouteFunction) # true

```
The `route` has predefined method that helps create the following operations and their names proceeds its operation

- GET
- POST
- PUT
- DELETE
- PATCH
- GENERIC-for operation combination eg: `methods=['POST', 'PATCH']`

## **Initialization Parameters**
-  ### **`path`**
it's a required uniques endpoint path string
 
-  ### **`methods`**
it's required a collection of endpoint operational mode eg: `['POST', 'PUT']`
 
-  ### **`auth`**
defines endpoint authentication method. default: `NOT_SET`
 
-  ### **`response`**
defines `dict[status_code, schema]` or `Schema`. It is used validated returned response. default: `NOT_SET`
 
-  ### **`operation_id`**
it is an optional unique id that distinguishes `operations` in path view. default: `NOT_SET`
 
-  ### **`summary`**
it is an optional summary that describes your endpoint. default: `None`
 
-  ### **`description`**
it is an optional description that describes your endpoint. default: `None`
 
-  ### **`tags`**
It is a list of strings useful for endpoint grouping for documentation purpose. default: `None`
 
-  ### **`deprecated`**
it is an optional boolean parameter that declares an endpoint deprecated. default: `None`
 
-  ### **`by_alias`**
it is an optional parameter that is applied to filter `response` schema object. default: `False`
 
-  ### **`exclude_unset`**
it is an optional parameter that is applied to filter `response` schema object. default: `False`
 
-  ### **`exclude_defaults`**
it is an optional parameter that is applied to filter `response` schema object. default: `False`
 
-  ### **`exclude_none`**
it is an optional parameter that is applied to filter `response` schema object. default: `False`
 
-  ### **`include_in_schema`**
indicates whether an endpoint should appear on the swagger documentation. default: `True`
 
-  ### **`url_name`**
it gives a name to an endpoint which can be resolved using `reverse` function in django. default: `None`
 
-  ### **`permissions`**
defines collection route permission classes. default: `None`

Most of these parameters are what is used in creating and endpoint in Django-Ninja, but it has been abstracted here to be for the same purpose on APIController class


## **Async Route Definition**
**Django-Ninja-Extra** `route` class also supports async endpoint definition just like in Django-Ninja.
This is only available on Django > 3.0.

For Example

```python
import asyncio
from ninja_extra import http_get, api_controller
from ninja_extra.controllers import AsyncRouteFunction

@api_controller
class MyController:
    @http_get("/say-after")
    async def say_after(self, delay: int, word: str):
        await asyncio.sleep(delay)
        return {'saying': word}

assert isinstance(MyController.say_after, AsyncRouteFunction) # true

```

!!! info
    Read more on Django-Ninja [Async Support](https://django-ninja.rest-framework.com/async-support/#quick-example)
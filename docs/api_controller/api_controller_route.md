# **APIController Route Decorator**
The `route` class is a function decorator designed to annotate a Controller class function as an endpoint with a specific HTTP method.

For instance:
```python
from ninja_extra import route, api_controller

@api_controller
class MyController:
    @route.get('/test')
    def test(self):
        return {'message': 'test'}

```
The `route` provides predefined methods that simplify the creation of various operations, and their names align with the respective HTTP methods:

- GET: `route.get`
- POST: `route.post`
- PUT: `route.put`
- DELETE: `route.delete`
- PATCH: `route.patch`
- GENERIC - for combinations of operations, e.g., `route.generic(methods=['POST', 'PATCH'])`


## **Initialization Parameters**
Here's a summarized description of the parameters for the `route` class in NinjaExtra:

- **`path`**: A required unique endpoint path string.

- **`methods`**: A collection of required HTTP methods for the endpoint, e.g., `['POST', 'PUT']`.

- **`auth`**: Defines the authentication method for the endpoint. Default: `NOT_SET`

- **`response`**: Defines the response format as `dict[status_code, schema]` or `Schema`. It is used to validate the returned response.Default: `NOT_SET`

- **`operation_id`**: An optional unique identifier distinguishing operations in path view.Default: `NOT_SET`

- **`summary`**: An optional summary describing the endpoint. Default: `None`

- **`description`**: An optional description providing additional details about the endpoint. Default: `None`

- **`tags`**: A list of strings for grouping the endpoint for documentation purposes. Default: `None`

- **`deprecated`**: An optional boolean parameter indicating if the endpoint is deprecated. Default: `None`

- **`by_alias`**: An optional parameter applied to filter the `response` schema object. Default: `False`

- **`exclude_unset`**: An optional parameter applied to filter the `response` schema object.  Default: `False`

- **`exclude_defaults`**: An optional parameter applied to filter the `response` schema object.  Default: `False`

- **`exclude_none`**: An optional parameter applied to filter the `response` schema object.  Default: `False`

- **`include_in_schema`**: Indicates whether the endpoint should appear on the Swagger documentation.  Default: `True`

- **`url_name`**: Gives a name to the endpoint that can be resolved using the `reverse` function in Django.  Default: `None`

- **`permissions`**: Defines a collection of route permission classes for the endpoint. Default: `None`

These parameters serve a similar purpose to those used in creating an endpoint in Django-Ninja 
but have been abstracted to apply to Controller classes in NinjaExtra.


## **Async Route Definition**
In **Django-Ninja-Extra**, the `route` class supports the definition of asynchronous endpoints, similar to Django-Ninja. 
This feature is available for Django versions greater than 3.0.

For example:

```python
import asyncio
from ninja_extra import http_get, api_controller

@api_controller
class MyController:
    @http_get("/say-after")
    async def say_after(self, delay: int, word: str):
        await asyncio.sleep(delay)
        return {'saying': word}
```

In this illustration, the `say_after` endpoint is defined as an asynchronous function using the `async` 
keyword, allowing for asynchronous operations within the endpoint.

!!! info
    Read more on Django-Ninja [Async Support](https://django-ninja.rest-framework.com/async-support/#quick-example)

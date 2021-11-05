# APIController

APIController is a borrowed term from C# environment. Controller is concept from MVC. 
Although Django is not an MVC framework, but we can mimic the concept generally.

The APIController is an abstract class model that allows you to expose some class instance functions as route functions.
It also supports dependency injection with **Injector** or **Django injector**.

```python
class APIController(ABC, metaclass=APIControllerModelSchemaMetaclass):
    ...
```

## Model Properties
### `permission_classes`
List of default permission classes. This can be overridden in route function. default: `[]`

### `auth`
List of default Authentication instances. As described in Django-Ninja [Authentication](https://django-ninja.rest-framework.com/tutorial/authentication/). default: `[]`

### `api`
Instance of NinjaExtraAPI at runtime. default:`None`

### `auto_import`
states whether APIController should added to auto_controller import list. default: `True`

### `get_router(cls) -> Optional[ControllerRouter]`
return controller to router instance if present and raises Exception is absent.

### `get_path_operations(cls) -> DictStrAny`
container `dict` of route definition which are pass to Django-Ninja at runtime

### `add_operation_from_route_function(cls, route_function: RouteFunction)`
A method overload for `add_api_operation` 

### `add_api_operation(cls, ...)`
Adds APIController route definitions to path operation

### `get_route_functions(cls) -> Iterator[RouteFunction]`
Gets all registered route in an APIController

### `get_permissions(self)`
Returns list of `permission_classes` instances

### `check_permissions(self)`
Check permission when route function is invoked

### `check_object_permissions(self, obj: Any)`
Checks object permissions. This is not automated. However, when called, it triggers all `permission_classes` `has_object_permission` function, just like in DRF


## APIController Route Decorator
To define an APIController function as route, it needs to be decorated with `route`
The `route` decorator is like `router` class in Django-Ninja but the behaviour is different.
Its main purpose is to define `route function` in APIController.

For example
```python
from ninja_extra import route, APIController
from ninja_extra.controllers import RouteFunction

class MyController(APIController):
    @route.get('/test')
    def test(self):
        return {'message': 'test'}

assert isinstance(MyController.test, RouteFunction) # true

```
The `route` class has the following operations
 - GET
 - POST
 - PUT
 - DELETE
 - PATCH
 - GENERIC - for operation combination eg: `methods=['POST', 'PATCH']`
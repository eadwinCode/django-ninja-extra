# **Controller**

APIController is a borrowed term from C# environment. Controller is concept from MVC. 
Although Django is not an MVC framework, but we can mimic the concept generally.

The APIController is an abstract class model that allows you to expose some class instance functions as route functions.
It also supports dependency injection with **Injector** or **Django injector**.

```python
class APIController(ABC, metaclass=APIControllerModelMetaclass):
    ...
```

## **Model Properties**
-  ### **`permission_classes`**
List of default permission classes defined in a controller `router`

-  ### **`auth`**
List of default Authentication instances. As described in Django-Ninja [Authentication](https://django-ninja.rest-framework.com/tutorial/authentication/). default: `[]`

-  ### **`api`**
Instance of NinjaExtraAPI at runtime. default:`None`

-  ### **`auto_import`**
states whether APIController should added to auto_controller import list. default: `True`

-  ### **`get_router(cls)`**
return controller to router instance if present and raises Exception is absent.

-  ### **`get_path_operations(cls)`**
container `dict` of route definition which are pass to Django-Ninja at runtime

-  ### **`add_operation_from_route_function(cls, route_function: RouteFunction)`**
A method overload for `add_api_operation` 

-  ### **`add_api_operation(cls, ...)`**
Adds APIController route definitions to path operation

-  ### **`get_route_functions(cls)`**
Gets all registered route in an APIController

-  ### **`get_permissions(self)`**
Returns list of `permission_classes` instances

-  ### **`check_permissions(self)`**
Check permission when route function is invoked

-  ### **`check_object_permissions(self, obj: Any)`**
Checks object permissions. This is not automated. However, when called, it triggers all `permission_classes` `has_object_permission` function, just like in DRF

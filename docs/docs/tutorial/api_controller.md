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


## Usage
Let's create an APIController to manage Django user model

```python
import uuid
from typing import List
from ninja import ModelSchema
from ninja_extra import APIController, route, router, exceptions, status
from ninja_extra.controllers.response import Detail
from django.contrib.auth import get_user_model


class UserSchema(ModelSchema):
    class Config:
        model = get_user_model()
        model_fields = ['username', 'email', 'first_name']


@router('/users')
class UsersController(APIController):
    user_model = get_user_model()

    @route.post('')
    def create_user(self, user: UserSchema):
        # just simulating created user
        return self.Id(uuid.uuid4())

    @route.generic('/{int:user_id}', methods=['put', 'patch'], response=UserSchema)
    def update_user(self, user_id: int):
        """ Django Ninja will serialize Django ORM model to schema provided as `response`"""
        user = self.user_model.objects.filter(id=user_id).first()
        if user:
            return user
        raise exceptions.NotFound(f'User with id: `{user_id}` not found')

    @route.delete('/{int:user_id}', response=Detail(status_code=status.HTTP_204_NO_CONTENT))
    def delete_user(self, user_id: int):
        user = self.user_model.objects.filter(id=user_id).first()
        if user:
            user.delete()
            return self.create_response('', status_code=status.HTTP_204_NO_CONTENT)
        raise exceptions.NotFound(f'User with id: `{user_id}` not found')
    
    @route.get('', response=List[UserSchema])
    def list_user(self):
        return self.user_model.objects.all()

    @route.get('/{user_id}', response=UserSchema)
    def get_user_by_id(self, user_id: int):
        user = self.user_model.objects.filter(id=user_id).first()
        if user:
            return user
        raise exceptions.NotFound(f'User with id: `{user_id}` not found')
```
# **Controller**

APIController is a borrowed term from the C# ASP.NET environment which is an MVC framework. Although Django is not an MVC framework, we can still mimic the concept generally just like any other programming concept.

Django-Ninja-Extra APIController is modelled after C# ASP.NET ApiController, giving all OOP sense in creating your controller models and adapting recent software design patterns in your Django project. 

### Why APIController in Django.
I come from a background where we model anything in class based object, and I have worked with many API tools out there in python: DRF, FastAPI, Flask-Restful. It is either function based or class tailored to function based.
Don't get me wrong, there are still great libraries. In fact, some features of Django-Ninja-Extra came from DRF. So I am a big fan. I needed more.

I enjoyed Django ORM and I missed it while working with FastAPI but Django-Ninja became a saving grace. It brought FastAPI to Django in one piece. And it's super fast.

So I designed APIController to extend Django-Ninja to class-based and have something more flexible to adapt to recent software design patterns out there.

So if you enjoy class-based controls for building API, welcome aboard.

## Quick Example
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

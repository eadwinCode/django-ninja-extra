# **Controller**
Ninja-Extra APIController is responsible for handling incoming requests and returning responses to the client.

In Ninja-Extra, there are major components to creating a controller model

- ControllerBase
- APIController Decorator

## ControllerBase

The `ControllerBase` class is the base class for all controllers in Django Ninja Extra. 
It provides the core functionality for handling requests, validating input, and returning responses in a class-based approach.

The class includes properties and methods that are common to all controllers, such as the `request` object, `permission_classes`, and `response` object which are part of the `RouteContext`. 
The request object contains information about the incoming request, such as headers, query parameters, and body data. 
The permission_classes property is used to define the permissions required to access the controller's routes, 
while the response object is used to construct the final response that is returned to the client.

In addition to the core properties, the `ControllerBase` class also includes a number of utility methods that can be used to handle common tasks such as object permission checking (`check_object_permission`), creating quick responses (`create_response`), and fetching data from database (`get_object_or_exception`). 
These methods can be overridden in subclasses to provide custom behavior.

The ControllerBase class also includes a **dependency injection** system that allows for easy access to other services and objects within the application, such as the repository services etc.

```python
from ninja_extra import ControllerBase, api_controller

@api_controller('/users')
class UserControllerBase(ControllerBase):
    ...
```

## APIController Decorator
The `api_controller` decorator is used to define a class-based controller in Django Ninja Extra. 
It is applied to a ControllerBase class and takes several arguments to configure the routes and functionality of the controller.

The first argument, `prefix_or_class`, is either a prefix string for grouping all routes registered under the controller or the class object that the decorator is applied on.

The second argument, `auth`, is a list of all Django Ninja Auth classes that should be applied to the controller's routes.

The third argument, `tags`, is a list of strings for OPENAPI tags purposes.

The fourth argument, `permissions`, is a list of all permissions that should be applied to the controller's routes.

The fifth argument, `auto_import`, defaults to true, which automatically adds your controller to auto import list.

for example:

```python
import typing
from ninja_extra import api_controller, ControllerBase, permissions, route
from django.contrib.auth.models import User
from ninja.security import APIKeyQuery
from ninja import ModelSchema


class UserSchema(ModelSchema):
    class Config:
        model = User
        model_fields = ['username', 'email', 'first_name']


@api_controller('users/', auth=[APIKeyQuery()], permissions=[permissions.IsAuthenticated])
class UsersController(ControllerBase):
    @route.get('', response={200: typing.List[UserSchema]})
    def get_users(self):
        # Logic to handle GET request to the /users endpoint
        users = User.objects.all()
        return users

    @route.post('create/', response={200: UserSchema})
    def create_user(self, payload: UserSchema):
        # Logic to handle POST request to the /users endpoint
        new_user = User.objects.create(
            username=payload.username,
            email=payload.email,
            first_name=payload.first_name,
        )
        new_user.set_password('password')
        return new_user

```

In the above code, we have defined a controller called `UsersController` using the `api_controller` decorator. 
The decorator is applied to the class and takes two arguments, the URL endpoint `/users` and `auth` and `permission` classes. 
And `get_users` and `create_user` are route function that handles GET `/users` and POST `/users/create` incoming request.


!!!info
    Inheriting from ControllerBase class gives you more IDE intellisense support.

## Quick Example

Let's create an APIController to properly manage Django user model

```python
import uuid
from ninja import ModelSchema
from ninja_extra import (
    http_get, http_post, http_generic, http_delete,
    api_controller, status, ControllerBase, pagination
)
from ninja_extra.controllers.response import Detail
from django.contrib.auth import get_user_model


class UserSchema(ModelSchema):
    class Config:
        model = get_user_model()
        model_fields = ['username', 'email', 'first_name']


@api_controller('/users')
class UsersController(ControllerBase):
    user_model = get_user_model()

    @http_post()
    def create_user(self, user: UserSchema):
        # just simulating created user
        return self.Id(uuid.uuid4())

    @http_generic('/{int:user_id}', methods=['put', 'patch'], response=UserSchema)
    def update_user(self, user_id: int):
        """ Django Ninja will serialize Django ORM model to schema provided as `response`"""
        user = self.get_object_or_exception(self.user_model, id=user_id)
        return user

    @http_delete('/{int:user_id}', response=Detail(status_code=status.HTTP_204_NO_CONTENT))
    def delete_user(self, user_id: int):
        user = self.get_object_or_exception(self.user_model, id=user_id)
        user.delete()
        return self.create_response('', status_code=status.HTTP_204_NO_CONTENT)

    @http_get("", response=pagination.PaginatedResponseSchema[UserSchema])
    @pagination.paginate(pagination.PageNumberPaginationExtra, page_size=50)
    def list_user(self):
        return self.user_model.objects.all()

    @http_get('/{user_id}', response=UserSchema)
    def get_user_by_id(self, user_id: int):
        user = self.get_object_or_exception(self.user_model, id=user_id)
        return user
```

In the example above, the `UsersController` class defines several methods that correspond to different HTTP methods, 
such as `create_user`, `update_user`, `delete_user`, `list_user` and `get_user_by_id`. 
These methods are decorated with `http_post`, `http_generic`, `http_delete`, `http_get` decorators respectively.

The `create_user` method uses `http_post` decorator and accepts a user argument of type `UserSchema`, 
which is a `ModelSchema` that is used to validate and serialize the input data. 
The method is used to create a new user in the system and return an `ID` of the user.

The `update_user` method uses `http_generic` decorator and accepts a `user_id` argument of type int. 
The decorator is configured to handle both `PUT` and `PATCH` methods and 
provides a response argument of type `UserSchema` which will be used to serialize the user object.

The `delete_user` method uses `http_delete` decorator and accepts a `user_id` argument of type int and a response argument of type 
Detail which will be used to return a 204 status code with an empty body on success.

The `list_user` method uses `http_get` decorator and decorated with `pagination.paginate` decorator that paginate the results of the method using `PageNumberPaginationExtra` class with page_size=50. 
It also provides a response argument of type `pagination.PaginatedResponseSchema[UserSchema]` which will be used to serialize and paginate the list of users returned by the method.

The `get_user_by_id` method uses `http_get` decorator and accepts a `user_id` argument of type int and a response argument of type UserSchema which will be used to serialize the user object.

The UsersController also use `self.get_object_or_exception(self.user_model, id=user_id)` which is a helper method that will raise an exception if the user object is not found.

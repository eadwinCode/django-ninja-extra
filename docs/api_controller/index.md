# **Controller**

APIController is a borrowed term from the C# ASP.NET environment which is an MVC framework. Although Django is not an MVC framework, we can still mimic the concept generally just like any other programming concept.

Django-Ninja-Extra APIController is modelled after C# ASP.NET ApiController, giving all OOP sense in creating your controller models and adapting recent software design patterns in your Django project. 

### Why APIController in Django.
I come from a background where we model anything in class based object, and I have worked with many API tools out there in python: DRF, FastAPI, Flask-Restful. It is either function based or class tailored to function based.
Don't get me wrong, there are still great libraries. In fact, some features of Django-Ninja-Extra came from DRF. So I am a big fan. I needed more.

I enjoyed Django ORM and I missed it while working with FastAPI but Django-Ninja became a saving grace. It brought FastAPI to Django in one piece. And it's super fast.

So I designed APIController to extend Django-Ninja to class-based and have something more flexible to adapt to recent software design patterns out there.

So if you enjoy class-based controls for building API, welcome aboard.


## ControllerBase
```python
class ControllerBase(ABC):
    ...
```
APIController decorates any class with `ControllerBase` if its not inheriting from it.

!!!info
    Inheriting from ControllerBase class gives you more IDE intellisense support.

## Quick Example
Let's create an APIController to manage Django user model

```python
import uuid
from typing import List
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

    @http_post('')
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
    
    @http_get('', response=List[UserSchema])
    @pagination.paginate
    def list_user(self):
        return self.user_model.objects.all()

    @http_get('/{user_id}', response=UserSchema)
    def get_user_by_id(self, user_id: int):
        user = self.get_object_or_exception(self.user_model, id=user_id)
        return user
```

# **Tutorial / Reference**

This tutorial shows you how to use **Django Ninja Extra** with most of its features. 
And most especially assumes you know how to use **Django Ninja**


!!! info
    A lot of content here is drawn from Django-Ninja. So a lot would make sense if you understand the Django-Ninja framework first.

## **Installation**

```
pip install django-ninja-extra
```

After installation, add `ninja_extra` to your `INSTALLED_APPS`

```Python 
INSTALLED_APPS = [
    ...,
    'ninja_extra',
]
```


## **Create a Django project**

(If you already have an existing Django project, skip to the next step).

Start a new Django project (or use an existing one).

```
django-admin startproject myproject
```


## **First steps**

Let's create a module for our API.  Create an **api.py** file in the same directory location as **urls.py**:


`api.py`


```Python
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI()

# function definition using Django-Ninja default router
@api.get("/hello")
def hello(request):
    return "Hello world"

```

Now go to **urls.py** and add the following:


```Python hl_lines="3 7"
from django.contrib import admin
from django.urls import path
from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
```

## **Defining operation methods**
"Operation" can be one of the HTTP "methods":

 - GET
 - POST
 - PUT
 - DELETE
 - PATCH
 - ... and more.

These are Django-Ninja defined operations on the API or Django-Ninja router. 
The same operation is exposed to APIControllers with the `route` class. 
The `route` class is an extra decorator that converts APIController instance methods to route function or endpoint.

On the other hand, the `router` here is a short form of the `ControllerRouter` class,  an adapter class, which is an that only adapts APIController to the Django-Ninja router. It also provides global control of all routes defined in any APIController class.
```Python
from ninja_extra import (
    api_controller, 
    http_get, http_post, http_put, http_delete, http_patch, http_generic
)
from ninja.constants import NOT_SET

@api_controller('', tags=['My Operations'], auth=NOT_SET, permissions=[])
class MyAPIController:
    @http_get("/path")
    def get_operation(self):
        ...
    
    @http_post("/path")
    def post_operation(self):
        ...
    
    @http_put("/path")
    def put_operation(self):
        ...
    
    @http_delete("/path")
    def delete_operation(self):
        ...
    
    @http_patch("/path")
    def patch_operation(self):
        ...
    
    # If you need to handle multiple methods with a single function, you can use the `generic` method as shown above
    @http_generic(["POST", "PATCH"]) 
    def mixed(request):
        ...

api.register_controllers(MyAPIController)
```
To have a complete Controller setup, the APIController must be decorated with `ControllerRouter` before it's been registered.


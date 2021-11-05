# Tutorial - Intro

This tutorial shows you how to use **Django Ninja Extra** with most of its features. 
It is also built to work as reference documentation.

This tutorial assumes that you know at least some basics of the <a href="https://www.djangoproject.com/" target="_blank">Django Framework</a>, like how to create a project and run it.


## Installation

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


## Create a Django project

(If you already have an existing Django project, skip to the next step).

Start a new Django project (or use an existing one).

```
django-admin startproject myproject
```


## First steps

Let's create a module for our API.  Create an **api.py** file in the same directory location as **urls.py**:


`api.py`


```Python
from ninja_extra import NinjaExtraAPI, route, APIController, router

api = NinjaExtraAPI()


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

## Defining operation methods

"Operation" can be one of the HTTP "methods":

 - GET
 - POST
 - PUT
 - DELETE
 - PATCH
 - ... and more


**Django Ninja Extra** comes with an extra decorator `route` for defining route function in your controller class:
**Django Ninja Extra** APIController can only works when wrapped around `ControllerRouter` which is the same as `router`
The `router` give you global control of all routes defined in a controller.

```Python
@router('', tags=['My Operations'], auth=NOT_SET, permissions=[])
class MyAPIController(APIController):
    @route.get("/path")
    def get_operation(self):
        ...
    
    @route.post("/path")
    def post_operation(self):
        ...
    
    @route.put("/path")
    def put_operation(self):
        ...
    
    @route.delete("/path")
    def delete_operation(self):
        ...
    
    @route.patch("/path")
    def patch_operation(self):
        ...
    
    @route.generic(["POST", "PATCH"])
    def mixed(request):
        ...
```

If you need to handle multiple methods with a single function, you can use the `generic` method as shown above

**Django Ninja Extra** APIController only works when wrapped around `ControllerRouter` which is the same as `router`


# **APIController Router**

The `ControllerRouter` which is `router` in short form, adapts APIController classes to Django-Ninja router.
During `api.register_controllers` call, the APIController `_router` is pass to the Django-Ninja for route processing.
For this reason, APIController class can't be registered without having a `ControllerRouter` decoration

## **Controller Router Initialization Parameters**
-  ### **`prefix`**
it is a required parameter that defines extra route prefix for all route functions defined in an APIController class

-  ### **`auth`**
It is an optional parameter that defines global `auth` for APIController classes. This can be overridden by `route` `auth` definition. default: `NOT_SET`

-  ### **`tags`**
It is an optional parameter that defines global `tags` for APIController classes. This can be overridden by `route` `tags` definition. default: `None`

-  ### **`permissions`**
It is an optional parameter that defines global `permissions` APIController classes. This can be overridden by `route` `permissions` definition. default: `None`

-  ### **`controller: Optional[Type["APIController"]]`**
It is APIController class decorated

## **Quick Usage**
```python
from ninja.constants import NOT_SET
from ninja_extra import APIController, router, NinjaExtraAPI
 
router = router(prefix='', auth=NOT_SET, tags=['someTags'], permissions=[])

@router
class MyRouterController(APIController):
    '''testing'''

api = NinjaExtraAPI()
api.register_controllers(MyRouterController)
```
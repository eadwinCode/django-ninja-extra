
Route path _parameters_ are declared in python format-strings.
for example:

```python hl_lines="7 8"
from ninja_extra import APIController, route, router
from ninja import constants


@router('', tags=['My Operations'], auth=constants.NOT_SET, permissions=[])
class MyAPIController(APIController):
    @route.get('/users/{user_id}')
    def get_user_by_id(self, user_id: int):
        return {'user_id': user_id}
```

The value of the path parameter `user_id` will be passed to your function as the argument `user_id`.

!!! info
    Read [more](https://django-ninja.rest-framework.com/tutorial/path-params/)
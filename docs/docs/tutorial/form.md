
If you are not sure how to make a form post request like `application/x-www-form-urlencode` or `multipart/form-data` in django-ninja-extra, then this guide would be useful for you.
Django-Ninja already covers most of the use cases [here](https://django-ninja.rest-framework.com/tutorial/form-params/), but I will give you a quick summary here.

### Form Data as Params

```python hl_lines="7 8"
from ninja import Form, constants
from ninja_extra import APIController, route, router


@router('', tags=['My Operations'], auth=constants.NOT_SET, permissions=[])
class MyAPIController(APIController):
    @route.post("/login")
    def login(self, username: str = Form(...), password: str = Form(...)):
        return {'username': username, 'password': '*****'}
```
Two things to note here:

- You need to import `Form` from `ninja` module
- Use `Form` as default value for your parameter


!!! info
    For more information on this, visit [Django-Ninja Form tutorial](https://django-ninja.rest-framework.com/tutorial/form-params/)
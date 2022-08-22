# **Pagination**

**Django Ninja Extra** provides an intuitive pagination model using `paginate` decoration from the Django-Ninja-Extra pagination module. It expects a List or Queryset from as a route function result.

## **Properties**

`def paginate(func_or_pgn_class: Any = NOT_SET, **paginator_params: Any) -> Callable[..., Any]:`

- func_or_pgn_class: Defines a route function or a Pagination Class. default: `ninja_extra.pagination.LimitOffsetPagination`
- paginator_params: extra parameters for initialising Pagination Class

!!! info
    When using `ninja_extra.pagination.LimitOffsetPagination`, you should use `NinjaPaginationResponseSchema` as pagination response schema wrapper
    eg: 
    ```python
    
    @route.get('', response=NinjaPaginationResponseSchema[UserSchema])
    @paginate()
    def list_items(self):
        return item_model.objects.all()
    ```

### Changing Default Pagination Class
To change the default pagination class, you need to add a `NINJA_EXTRA` variable in `settings.py` with a key `PAGINATION_CLASS` and value defining path to pagination class
```python
# Django project settings.py
INSTALLED_APPS = [
    ...
]
NINJA_EXTRA={
    'PAGINATION_CLASS': 'ninja_extra.pagination.PageNumberPaginationExtra'
}
```

## **Usage**
```python
from typing import List
from ninja_extra.pagination import (
    paginate, PageNumberPaginationExtra, PaginatedResponseSchema
)
from ninja_extra import api_controller, route, NinjaExtraAPI
from ninja import ModelSchema
from django.contrib.auth import get_user_model

user_model = get_user_model()


class UserSchema(ModelSchema):
    class Config:
        model = user_model
        model_fields = ['username', 'email']

        
@api_controller('/users')
class UserController:
    @route.get('', response=PaginatedResponseSchema[UserSchema])
    @paginate(PageNumberPaginationExtra, page_size=50)
    def get_users(self):
        return user_model.objects.all()
    
    @route.get('/limit', response=List[UserSchema])
    @paginate
    def get_users_with_limit(self):
        # this will use default paginator class - ninja_extra.pagination.LimitOffsetPagination
        return user_model.objects.all()

    
api = NinjaExtraAPI(title='Pagination Test')
api.register_controllers(UserController)
```

![Preview](../images/pagination_example.gif)

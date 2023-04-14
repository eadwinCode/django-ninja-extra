# **Ordering**

**Django Ninja Extra** provides an intuitive ordering model using `ordering` decoration from the Django-Ninja-Extra ordering module. It expects a Queryset or a List from as a route function result.

> This feature was inspired by the [DRF OrderingFilter](https://www.django-rest-framework.org/api-guide/filtering/#orderingfilter)

## **Properties**

`def ordering(func_or_ordering_class: Any = NOT_SET, **ordering_params: Any) -> Callable[..., Any]:`

- func_or_ordering_class: Defines a route function or an Ordering Class. default: `ninja_extra.ordering.Ordering`
- ordering_params: extra parameters for initialising Ordering Class

### Changing Default Ordering Class

To change the default ordering class, you need to add a `NINJA_EXTRA` variable in `settings.py` with a key `ORDERING_CLASS` and value defining path to ordering class

```python
# Django project settings.py
INSTALLED_APPS = [
    ...
]
NINJA_EXTRA={
    'ORDERING_CLASS': 'someapp.somemodule.CustomOrdering'
}
```

## **Usage**

- If you do not specify the `ordering_fields` parameter, all fields from the QuerySet will be used for ordering.
- For example, to order users by username:
  > http://example.com/api/users?ordering=username
- The client may also specify reverse orderings by prefixing the field name with '-', example:
  > http://example.com/api/users?ordering=-username
- Multiple orderings may also be specified:
  > http://example.com/api/users?ordering=username,email

```python
from typing import List
from ninja_extra.ordering import ordering, Ordering
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
    @route.get('', response=List[UserSchema])
    @ordering(Ordering, ordering_fields=['username', 'email'])
    def get_users(self):
        return user_model.objects.all()

    @route.get('/all-sort', response=List[UserSchema])
    @ordering
    def get_users_with_all_field_ordering(self):
        return [u for u in user_model.objects.all()]


api = NinjaExtraAPI(title='Ordering Test')
api.register_controllers(UserController)
```

## Note

> If you use the `paginate` decorator and the `ordering` decorator together, the `paginate` decorator should be above the `ordering` decorator because first the data are sorted and then the data are paginated, for example:
>
> ```python
>    @route.get('', response=List[UserSchema])
>    @paginate
>    @ordering(Ordering, ordering_fields=['username', 'email'])
>    def get_users(self):
>        return user_model.objects.all()
> ```

# **Searching**

**Django Ninja Extra** provides an intuitive searching model using `searching` decoration from the Django-Ninja-Extra searching module. It expects a Queryset or a List from as a route function result.

> This feature was inspired by the [DRF SearchFilter](https://www.django-rest-framework.org/api-guide/filtering/#searchfilter)

## **Properties**

`def searching(func_or_searching_class: Any = NOT_SET, **searching_params: Any) -> Callable[..., Any]:`

- func_or_searching_class: Defines a route function or an Searching Class. default: `ninja_extra.searching.Searching`
- searching_params: extra parameters for initialising Searching Class

### Changing Default Searching Class

To change the default searching class, you need to add a `NINJA_EXTRA` variable in `settings.py` with a key `SEARCHING_CLASS` and value defining path to searching class

```python
# Django project settings.py
INSTALLED_APPS = [
    ...
]
NINJA_EXTRA={
    'SEARCHING_CLASS': 'someapp.somemodule.CustomSearching'
}
```

## **Usage**

- If you do not specify the `search_fields` parameter, will return the result without change.
- For example, to search users by username or email:
  > http://example.com/api/users?search=someuser
- You can also perform a related lookup on a ForeignKey or ManyToManyField with the lookup API double-underscore notation:
  > search_fields = ['username', 'email', 'profile__profession']
- By default, searches will use case-insensitive partial matches.  The search parameter may contain multiple search terms, which should be whitespace and/or comma separated.  If multiple search terms are used then objects will be returned in the list only if all the provided terms are matched. The search behavior may be restricted by prepending various characters to the `search_fields`.

  * '^' Starts-with search.
  * '=' Exact matches.
  * '@' Full-text search.  (Currently only supported Django's [PostgreSQL backend](https://docs.djangoproject.com/en/stable/ref/contrib/postgres/search/).)
  * '$' Regex search.

  For example:

    > search_fields = ['=username', '=email']

```python
from typing import List
from ninja_extra.searching import searching, Searching
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
    @searching(Searching, search_fields=['username', 'email'])
    def get_users(self):
        return user_model.objects.all()

    @route.get('/iexact-email', response=List[UserSchema])
    @searching(search_fields=['=email'])
    def get_users_with_search_iexact_email(self):
        return [u for u in user_model.objects.all()]


api = NinjaExtraAPI(title='Searching Test')
api.register_controllers(UserController)
```

## Note

> If you use the `paginate` decorator, the `ordering` decorator and the `searching` decorator together, the `paginate` decorator should be above the `ordering` decorator and the `ordering` decorator should be above the `searching` decorator because first the data is filtered, then the data is sorted and then paginated:, for example:
>
> ```python
>    @route.get('', response=List[UserSchema])
>    @paginate
>    @ordering(Ordering, ordering_fields=['username', 'email'])
>    @searching(Searching, search_fields=['username', 'email'])
>    def get_users(self):
>        return user_model.objects.all()
> ```

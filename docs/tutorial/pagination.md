# **Pagination**

**Django Ninja Extra** provides an intuitive pagination model using `paginate` decoration from the Django-Ninja-Extra pagination module. It expects a List or Queryset from as a route function result.

## **Properties**

`def paginate(func_or_pgn_class: Any = NOT_SET, filter_schema: Optional[Type[FilterSchema]] = None, **paginator_params: Any) -> Callable[..., Any]:`

- func_or_pgn_class: Defines a route function or a Pagination Class. default: `ninja_extra.pagination.LimitOffsetPagination`
- filter_schema: Optional FilterSchema class from Django Ninja for filtering querysets before pagination
- paginator_params: extra parameters for initialising Pagination Class

### **Using Ninja LimitOffsetPagination**
When using `ninja_extra.pagination.LimitOffsetPagination`,
you should use `NinjaPaginationResponseSchema` as pagination response schema wrapper.
For example: 
```python
from ninja_extra.schemas import NinjaPaginationResponseSchema

...

@route.get('', response=NinjaPaginationResponseSchema[UserSchema])
@paginate()
def list_items(self):
    return item_model.objects.all()
```
    

### **Changing Default Pagination Class**
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

## **Pagination with Filtering**

You can combine pagination with Django Ninja's `FilterSchema` to provide both filtering and pagination capabilities. Filters are applied to the queryset **before** pagination.

!!! info "Learn More About FilterSchema"
    For comprehensive information about FilterSchema features, custom expressions, combining filters, and advanced filtering techniques, see the official Django Ninja documentation: [https://django-ninja.dev/guides/input/filtering/](https://django-ninja.dev/guides/input/filtering/)

### **Basic Filtering Example**

```python
from typing import Optional
from ninja import FilterSchema
from ninja_extra.pagination import paginate, PageNumberPaginationExtra, PaginatedResponseSchema
from ninja_extra import api_controller, route, NinjaExtraAPI
from ninja import ModelSchema
from myapp.models import Book


class BookSchema(ModelSchema):
    class Config:
        model = Book
        model_fields = ['id', 'title', 'author', 'price', 'published_date']


# Define a FilterSchema for your model
class BookFilterSchema(FilterSchema):
    title: Optional[str] = None
    author: Optional[str] = None
    min_price: Optional[float] = None


@api_controller('/books')
class BookController:
    @route.get('', response=PaginatedResponseSchema[BookSchema])
    @paginate(PageNumberPaginationExtra, filter_schema=BookFilterSchema, page_size=20)
    def list_books(self):
        return Book.objects.all()


api = NinjaExtraAPI(title='Books API')
api.register_controllers(BookController)
```

**Example API calls:**
- `GET /api/books/?page=1&page_size=20` - Paginated results
- `GET /api/books/?title=Python&page=1` - Filter by title and paginate
- `GET /api/books/?author=John&min_price=10&page=2` - Multiple filters with pagination

### **Advanced Filtering with Custom Lookups**

Use Django Ninja's `FilterLookup` annotation for more complex filtering:

```python
from typing import Annotated, Optional
from ninja import FilterSchema, FilterLookup


class AdvancedBookFilterSchema(FilterSchema):
    # Case-insensitive containment search
    title: Annotated[Optional[str], FilterLookup("title__icontains")] = None
    
    # Exact match on author name
    author: Annotated[Optional[str], FilterLookup("author__name__iexact")] = None
    
    # Greater than or equal to price
    min_price: Annotated[Optional[float], FilterLookup("price__gte")] = None
    
    # Less than or equal to price
    max_price: Annotated[Optional[float], FilterLookup("price__lte")] = None
    
    # Date range filtering
    published_after: Annotated[Optional[str], FilterLookup("published_date__gte")] = None


@api_controller('/books')
class BookController:
    @route.get('', response=PaginatedResponseSchema[BookSchema])
    @paginate(PageNumberPaginationExtra, filter_schema=AdvancedBookFilterSchema, page_size=20)
    def list_books(self):
        return Book.objects.all()
```

### **Using FilterSchema with Model Controllers**

FilterSchema can also be integrated with Model Controllers through the `ModelPagination` configuration:

```python
from ninja import FilterSchema
from ninja_extra.controllers import ModelControllerBase
from ninja_extra.controllers.model import ModelConfig, ModelPagination
from ninja_extra.pagination import PageNumberPaginationExtra
from myapp.models import Book


class BookFilterSchema(FilterSchema):
    title: Optional[str] = None
    author__name: Optional[str] = None
    price__gte: Optional[float] = None


class BookModelController(ModelControllerBase):
    model_config = ModelConfig(
        model=Book,
        pagination=ModelPagination(
            klass=PageNumberPaginationExtra,
            filter_schema=BookFilterSchema,
            paginator_kwargs={"page_size": 25}
        )
    )
```

This configuration automatically applies the FilterSchema to the `list` endpoint of your Model Controller.

### **How It Works**

1. **Query Parameters**: When a request is made, both filter and pagination parameters are extracted from query parameters
2. **Filtering**: The FilterSchema validates and applies filters to the queryset first
3. **Pagination**: The filtered results are then paginated according to the pagination parameters
4. **Response**: The paginated response includes filtered results with pagination metadata

### **OpenAPI Schema**

When using FilterSchema with pagination, the OpenAPI documentation automatically includes both filter parameters and pagination parameters, making your API self-documenting and easy to use.

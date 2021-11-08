# **Settings**
Some default configuration of NinjaExtra which can be overridden by defining `NinjaExtra` keyword in django `settings.py`
as shown below:

```python
# Django project settings.py


NINJA_EXTRA = {
    'PAGINATION_CLASS':"ninja_extra.pagination.PageNumberPaginationExtra",
    'PAGINATION_PER_PAGE': 100,
    'INJECTOR_MODULES': [],
}
```

`PAGINATION_CLASS`
=======================
This defines the default paginator class used by `paginate` decorator 
function when a paginator class is not defined.
default: `ninja_extra.pagination.LimitOffsetPagination`

`PAGINATION_PER_PAGE`
=======================
This defines the default page size in paginator class used by `paginate` decorator function when a page size is not defined.
default: `100`


`INJECTOR_MODULES`
=======================
These are list of strings that defines injector `module` paths to be 
bound to Injector instance at app start up. default: `[]`


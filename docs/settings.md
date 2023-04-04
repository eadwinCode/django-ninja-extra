# **Settings**

Django-Ninja-Extra has some settings that can be overridden by adding a `NINJA_EXTRA` field in Django `settings.py` with some key-value pair as shown below:

```python
# Django project settings.py


NINJA_EXTRA = {
    'PAGINATION_CLASS':"ninja_extra.pagination.PageNumberPaginationExtra",
    'PAGINATION_PER_PAGE': 100,
    'INJECTOR_MODULES': [],
    'THROTTLE_CLASSES': [
        "ninja_extra.throttling.AnonRateThrottle",
        "ninja_extra.throttling.UserRateThrottle",
    ],
    'THROTTLE_RATES': {
        'user': '1000/day',
        'anon': '100/day',
    },
    'NUM_PROXIES': None,
    'ORDERING_CLASS':"ninja_extra.ordering.Ordering",
    'SEARCHING_CLASS':"ninja_extra.searching.Search",
}
```

You can override what you don't need. It is not necessary need to override everything.

# `PAGINATION_CLASS`

It defines the default paginator class used by the `paginate` decorator
function if a paginator class is not defined.
default: `ninja_extra.pagination.LimitOffsetPagination`

# `PAGINATION_PER_PAGE`

It defines the default page size that is passed to the `PAGINATION_CLASS` during instantiation.
default: `100`

# `INJECTOR_MODULES`

It contains a list of strings that defines the path to injector `Module`.
default: `[]`

# `THROTTLE_CLASSES`

It contains a list of strings that defines the path default throttling classes.
default: `[
    "ninja_extra.throttling.AnonRateThrottle",
    "ninja_extra.throttling.UserRateThrottle",
]`

# `THROTTLE_RATES`

It contains a key-value pair of different throttling rates which are applies to different `THROTTLING_CLASSES`.
default: `{
    'user': '1000/day',
    'anon': '100/day',
}`

# `ORDERING_CLASS`

It defines the default ordering class used by the `ordering` decorator
function if a ordering class is not defined.
default: `ninja_extra.ordering.Ordering`

# `SEARCHING_CLASS`

It defines the default searching class used by the `searching` decorator
function if a searching class is not defined.
default: `ninja_extra.searching.Searching`

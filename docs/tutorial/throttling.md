# **Throttling**

Throttling can be seen as a permission that determines if a request should be authorized. 
It indicates a temporary state used to control the rate of requests that clients can make to an API.

```python
from ninja_extra import NinjaExtraAPI, throttle
api = NinjaExtraAPI()

@api.get('/users')
@throttle  # this will apply default throttle classes [UserRateThrottle, AnonRateThrottle]
def my_throttled_endpoint(request):
    return 'foo'
```

!!! info
    The above example won't be throttled because the default scope for `UserRateThrottle` and `AnonRateThrottle`
    is `none`

## **Multiple Throttling**
Django-ninja-extra throttle supposes multiple throttles which is useful to impose different
constraints, which could be burst throttling rate or sustained throttling rates, on an API.
for example, you might want to limit a user to a maximum of 60 requests per minute, and 1000 requests per day.

```python
from ninja_extra import NinjaExtraAPI, throttle
from ninja_extra.throttling import UserRateThrottle
api = NinjaExtraAPI()

class User60MinRateThrottle(UserRateThrottle):
    rate = "60/min"
    scope = "minutes"


class User1000PerDayRateThrottle(UserRateThrottle):
    rate = "1000/day"
    scope = "days"

@api.get('/users')
@throttle(User60MinRateThrottle, User1000PerDayRateThrottle)
def my_throttled_endpoint(request):
    return 'foo'

```
## **Throttling Policy Settings**
You can set globally default throttling classes and rates in your project `settings.py` by overriding the keys below:
```python
# django settings.py
NINJA_EXTRA = {
    'THROTTLE_CLASSES': [
        "ninja_extra.throttling.AnonRateThrottle",
        "ninja_extra.throttling.UserRateThrottle",
    ],
    'THROTTLE_RATES': {
        'user': '1000/day',
        'anon': '100/day',
    },
    'NUM_PROXIES': None
}
```
The rate descriptions used in `THROTTLE_RATES` may include `second`, `minute`, `hour` or `day` as the throttle period.

```python
from ninja_extra import NinjaExtraAPI, throttle
from ninja_extra.throttling import UserRateThrottle

api = NinjaExtraAPI()

@api.get('/users')
@throttle(UserRateThrottle)
def my_throttled_endpoint(request):
    return 'foo'
```

## **Clients Identification**
Clients are identified by x-Forwarded-For in HTTP header and REMOTE_ADDR from WSGI variable.
These are unique identities which identifies clients IP addresses used for throttling.
`X-Forwarded-For` is preferable over `REMOTE_ADDR` and is used as so.

#### **Limit Clients Proxies**
If you need to strictly identify unique client IP addresses, you'll need to first configure the number of application proxies that the API runs behind by setting the `NUM_PROXIES` setting. This setting should be an integer of zero or more.
If set to non-zero then the client IP will be identified as being the last IP address in the X-Forwarded-For header, once any application proxy IP addresses have first been excluded. If set to zero, then the REMOTE_ADDR value will always be used as the identifying IP address.
It is important to understand that if you configure the `NUM_PROXIES` setting, then all clients behind a unique [NAT'd](https://en.wikipedia.org/wiki/Network_address_translation) gateway will be treated as a single client.

!!! info
    Further context on how the X-Forwarded-For header works, and identifying a remote client IP can be found here.

## **Throttling Model Cache setup**
The throttling models used in django-ninja-extra utilizes Django cache backend. It uses the `default` value of [`LocMemCache`]()
See Django's [cache documentation](https://docs.djangoproject.com/en/stable/topics/cache/#setting-up-the-cache) for more details.

If you dont want to use the default cache defined in throttle model, here is an example on how to define a different cache for a throttling model
```python

from django.core.cache import caches
from ninja_extra.throttling import AnonRateThrottle


class CustomAnonRateThrottle(AnonRateThrottle):
    cache = caches['alternate']
```
# **API Reference**

## **AnonRateThrottle**
`AnonRateThrottle` model is for throttling unauthenticated users using their IP address as key to throttle against.
It is suitable for restricting rate of requests from an unknown source

Request Permission is determined by:
- `rate` defined in derived class
- `anon` scope defined in `THROTTLE_RATES` in `NINJA_EXTRA` settings in `settings.py` 

## **UserRateThrottle**
`UserRateThrottle` model is for throttling authenticated users using user id or pk to generate a key to throttle against.
Unauthenticated requests will fall back to using the IP address of the incoming request to generate a unique key to throttle against.

Request Permission is determined by:
- `rate` defined in derived class
- `user` scope defined in `THROTTLE_RATES` in `NINJA_EXTRA` settings in `settings.py` 

You can use multiple user throttle rates for a `UserRateThrottle` model, for example:
```python
# example/throttles.py
from ninja_extra.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'
```

```python
# django settings.py
NINJA_EXTRA = {
    'THROTTLE_CLASSES': [
        'example.throttles.BurstRateThrottle',
        'example.throttles.SustainedRateThrottle'
    ],
    'THROTTLE_RATES': {
        'burst': '60/min',
        'sustained': '1000/day'
    }
}
```
## **DynamicRateThrottle**
`DynamicRateThrottle` model is for throttling authenticated and unauthenticated users in similar way as `UserRateThrottle`. 
Its key feature is in the ability to dynamically set `scope` where its used.
for an example:
we can defined a scope in settings

```python
# django settings.py
NINJA_EXTRA = {
    'THROTTLE_RATES': {
        'burst': '60/min',
        'sustained': '1000/day'
    }
}
```

```python
# api.py
from ninja_extra import NinjaExtraAPI, throttle
from ninja_extra.throttling import DynamicRateThrottle
api = NinjaExtraAPI()

@api.get('/users')
@throttle(DynamicRateThrottle, scope='burst')
def get_users(request):
    return 'foo'

@api.get('/users/<int:id>')
@throttle(DynamicRateThrottle, scope='sustained')
def get_user_by_id(request, id: int):
    return 'foo'
```
Here, we dynamically applied `sustained` rates and `burst` rates to `get_users` and `get_user_by_id` respectively


!!! info "new in v0.15.8"
    You can throttle all controller endpoints actions at the controller class level

## **Controller Throttling**

```python
# api.py
from ninja_extra import (
    NinjaExtraAPI, throttle, api_controller, ControllerBase,
    http_get
)
from ninja_extra.throttling import DynamicRateThrottle
api = NinjaExtraAPI()

@api_controller("/throttled-controller")
class ThrottlingControllerSample(ControllerBase):
    throttling_classes = [
        DynamicRateThrottle,
    ]
    throttling_init_kwargs = dict(scope="sustained")

    @http_get("/endpoint_1")
    @throttle(DynamicRateThrottle, scope='burst')
    def endpoint_1(self, request):
        # this will override the generally throttling applied at the controller
        return "foo"

    @http_get("/endpoint_2")
    def endpoint_2(self, request):
        return "foo"

    @http_get("/endpoint_3")
    def endpoint_3(self, request):
        return "foo"


api.register_controllers(ThrottlingControllerSample)
```
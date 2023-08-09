"""
Provides various throttling policies.
From DjangoRestFramework - https://github.com/encode/django-rest-framework/blob/master/rest_framework/throttling.py
"""
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from django.core.cache import cache as default_cache
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from ninja_extra.conf import settings


class BaseThrottle:
    """
    Rate throttling of requests.
    """

    THROTTLE_RATES: Optional[Dict] = None

    def __init__(self) -> None:
        self.key: Optional[str] = None

        self.history: List[float] = []
        self.now: float = 0.0
        self.num_requests: Optional[int] = None
        self.duration: Optional[int] = None

    def allow_request(self, request: HttpRequest) -> bool:
        """
        Return `True` if the request should be allowed, `False` otherwise.
        """
        raise NotImplementedError(".allow_request() must be overridden")

    def get_ident(self, request: HttpRequest) -> Optional[str]:
        """
        Identify the machine making the request by parsing HTTP_X_FORWARDED_FOR
        if present and number of proxies is > 0. If not use all of
        HTTP_X_FORWARDED_FOR if it is available, if not use REMOTE_ADDR.
        """
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        remote_addr = request.META.get("REMOTE_ADDR")
        num_proxies = settings.NUM_PROXIES

        if num_proxies is not None:
            if num_proxies == 0 or xff is None:
                return remote_addr
            addrs = xff.split(",")
            client_addr = addrs[-min(num_proxies, len(addrs))]
            return cast(str, client_addr.strip())

        return "".join(xff.split()) if xff else remote_addr

    def wait(self) -> Optional[float]:  # pragma: no cover
        """
        Optionally, return a recommended number of seconds to wait before
        the next request.
        """
        return None


class SimpleRateThrottle(BaseThrottle):
    """
    A simple cache implementation, that only requires `.get_cache_key()`
    to be overridden.

    The rate (requests / seconds) is set by a `rate` attribute on the Throttle
    class.  The attribute is a string of the form 'number_of_requests/period'.

    Period should be one of: ('s', 'sec', 'm', 'min', 'h', 'hour', 'd', 'day')

    Previous request information used for throttling is stored in the cache.
    """

    cache: Any = default_cache
    timer: Callable[[], float] = time.time
    cache_format: str = "throttle_%(scope)s_%(ident)s"
    scope: Optional[str] = None

    def __init__(self) -> None:
        super(SimpleRateThrottle, self).__init__()
        if not getattr(self, "rate", None):
            self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_cache_key(self, request: HttpRequest) -> Optional[str]:
        """
        Should return a unique cache-key which can be used for throttling.
        Must be overridden.

        May return `None` if the request should not be throttled.
        """
        raise NotImplementedError(".get_cache_key() must be overridden")

    def get_rate(self) -> Optional[str]:
        """
        Determine the string representation of the allowed request rate.
        """
        if not self.scope:
            msg = (
                "You must set either `.scope` or `.rate` for '%s' throttle"
                % self.__class__.__name__
            )
            raise ImproperlyConfigured(msg)

        _THROTTLE_RATES = self.THROTTLE_RATES or settings.THROTTLE_RATES
        try:
            return _THROTTLE_RATES[self.scope]
        except KeyError as e:
            msg = "No default throttle rate set for '%s' scope" % self.scope
            raise ImproperlyConfigured(msg) from e

    def parse_rate(
        self, rate: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Given the request rate string, return a two tuple of:
        <allowed number of requests>, <period of time in seconds>
        """
        if rate is None:
            return None, None
        num, period = rate.split("/")
        num_requests = int(num)
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period[0]]
        return num_requests, duration

    def allow_request(self, request: HttpRequest) -> bool:
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while (
            self.history and self.history[-1] <= self.now - self.duration  # type:ignore
        ):
            self.history.pop()
        if len(self.history) >= self.num_requests:  # type:ignore
            return self.throttle_failure()
        return self.throttle_success()

    def throttle_success(self) -> bool:
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        self.history.insert(0, self.now)
        self.cache.set(self.key, self.history, self.duration)
        return True

    def throttle_failure(self) -> bool:
        """
        Called when a request to the API has failed due to throttling.
        """
        return False

    def wait(self) -> Optional[float]:
        """
        Returns the recommended next request time in seconds.
        """
        assert self.duration is not None and self.num_requests is not None

        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1
        if available_requests <= 0:
            return None

        return remaining_duration / float(available_requests)


class AnonRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that may be made by a anonymous users.

    The IP address of the request will be used as the unique cache key.
    """

    scope = "anon"

    def get_cache_key(self, request: HttpRequest) -> Optional[str]:
        if request.user and request.user.is_authenticated:
            return None  # Only throttle unauthenticated requests.

        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class UserRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that may be made by a given user.

    The user id will be used as a unique cache key if the user is
    authenticated.  For anonymous requests, the IP address of the request will
    be used.
    """

    scope = "user"

    def get_cache_key(self, request: HttpRequest) -> Optional[str]:
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class DynamicRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls by different amounts for various parts of
    the API. Set Throttle scope dynamically for an api endpoint
    """

    def __init__(self, scope: Optional[str] = None) -> None:
        self.scope = scope
        super().__init__()

    def get_cache_key(self, request: HttpRequest) -> Optional[str]:
        """
        If `scope` is not set during initialization, don't apply this throttle.

        Otherwise generate the unique cache key by concatenating the user id
        with the `.throttle_scope` property of the view.
        """
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}

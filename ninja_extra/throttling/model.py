import time
from typing import Any, Callable, Dict, List, Optional

from django.core.cache import cache as default_cache
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from ninja.throttling import SimpleRateThrottle as BaseSimpleRateThrottle

from ninja_extra.lazy import settings_lazy


class SimpleRateThrottle(BaseSimpleRateThrottle):
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

    def __init__(self, rate: Optional[str] = None) -> None:
        if not rate and hasattr(self, "rate"):
            rate = getattr(self, "rate", None)
        super(SimpleRateThrottle, self).__init__(rate)

    def get_throttling_rates(self) -> Dict[str, Optional[str]]:
        rates = self.THROTTLE_RATES.copy()
        rates.update(settings_lazy().THROTTLE_RATES)

        return rates

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

        _THROTTLE_RATES = self.get_throttling_rates()
        try:
            return _THROTTLE_RATES[self.scope]
        except KeyError as e:
            msg = "No default throttle rate set for '%s' scope" % self.scope
            raise ImproperlyConfigured(msg) from e

    def allow_request(self, request: HttpRequest) -> bool:
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        return super().allow_request(request)

    def get_ident(self, request: HttpRequest) -> Optional[str]:
        """
        Identify the machine making the request by parsing HTTP_X_FORWARDED_FOR
        if present and number of proxies is > 0. If not use all of
        HTTP_X_FORWARDED_FOR if it is available, if not use REMOTE_ADDR.
        """

        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        remote_addr = request.META.get("REMOTE_ADDR")
        num_proxies = settings_lazy().NUM_PROXIES

        if num_proxies is not None:
            if num_proxies == 0 or xff is None:
                return remote_addr
            addrs: List[str] = xff.split(",")
            client_addr = addrs[-min(num_proxies, len(addrs))]
            return client_addr.strip()

        return "".join(xff.split()) if xff else remote_addr


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

    def __init__(self, rate: Optional[str] = None, scope: Optional[str] = None) -> None:
        self.scope = scope
        super().__init__(rate)

    def get_cache_key(self, request: HttpRequest) -> Optional[str]:
        """
        If `scope` is not set during initialization, don't apply this throttle.

        Otherwise, generate the unique cache key by concatenating the user id
        with the `.throttle_scope` property of the view.
        """
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}

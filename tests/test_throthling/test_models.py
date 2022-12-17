import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from ninja_extra.conf import settings
from ninja_extra.throttling import (
    AnonRateThrottle,
    BaseThrottle,
    DynamicRateThrottle,
    SimpleRateThrottle,
    UserRateThrottle,
)


@pytest.mark.django_db
class TestAnonRateThrottle:
    def setup_method(self):
        self.throttle = AnonRateThrottle()
        self.request = HttpRequest()
        self.request.user = None

    def test_authenticated_user_not_affected(self):
        user = User.objects.create(username="test")
        self.request.user = user
        assert self.throttle.get_cache_key(self.request) is None

    def test_get_cache_key_returns_correct_value(self):
        cache_key = self.throttle.get_cache_key(self.request)
        assert cache_key == "throttle_anon_None"


class TestBaseThrottle:
    def setup_method(self):
        self.throttling = BaseThrottle()
        self.request = HttpRequest()

    def test_allow_request_raises_not_implemented_error(self):
        with pytest.raises(NotImplementedError):
            self.throttling.allow_request(self.request)

    def test_get_ident_x_forward_for_works(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "2.2.2.2"
        ident = self.throttling.get_ident(self.request)
        assert ident == "2.2.2.2"
        self.request.META["HTTP_X_FORWARDED_FOR"] = "2.2.2.2, 1.1.1.1, 0.0.0.0"
        ident = self.throttling.get_ident(self.request)
        assert ident == "2.2.2.2,1.1.1.1,0.0.0.0"

    def test_get_ident_remote_forward_for_works(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = None
        self.request.META["REMOTE_ADDR"] = "2.2.2.2"
        ident = self.throttling.get_ident(self.request)
        assert ident == "2.2.2.2"

    def test_get_ident_with_num_proxies(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(settings, "NUM_PROXIES", 0)
            ident = self.throttling.get_ident(self.request)
            assert ident is None
            self.request.META["REMOTE_ADDR"] = "2.2.2.2"
            ident = self.throttling.get_ident(self.request)
            assert ident == "2.2.2.2"
        with monkeypatch.context() as m:
            m.setattr(settings, "NUM_PROXIES", 1)
            self.request.META["HTTP_X_FORWARDED_FOR"] = "2.2.2.2, 1.1.1.1, 0.0.0.0"
            ident = self.throttling.get_ident(self.request)
            assert ident == "0.0.0.0"

        with monkeypatch.context() as m:
            m.setattr(settings, "NUM_PROXIES", 2)
            self.request.META["HTTP_X_FORWARDED_FOR"] = "2.2.2.2, 1.1.1.1, 0.0.0.0"
            ident = self.throttling.get_ident(self.request)
            assert ident == "1.1.1.1"


class TestSimpleRateThrottle:
    def setup_method(self):
        SimpleRateThrottle.scope = "anon"

    def test_get_rate_raises_error_if_scope_is_missing(self):
        throttle = SimpleRateThrottle()
        with pytest.raises(ImproperlyConfigured):
            throttle.scope = None
            throttle.get_rate()

    def test_throttle_raises_error_if_rate_is_missing(self):
        SimpleRateThrottle.scope = "invalid scope"
        with pytest.raises(ImproperlyConfigured):
            SimpleRateThrottle()

    def test_parse_rate_returns_tuple_with_none_if_rate_not_provided(self):
        rate = SimpleRateThrottle().parse_rate(None)
        assert rate == (None, None)

    def test_allow_request_returns_true_if_rate_is_none(self):
        assert SimpleRateThrottle().allow_request(request=HttpRequest()) is True

    def test_get_cache_key_raises_not_implemented_error(self):
        with pytest.raises(NotImplementedError):
            SimpleRateThrottle().get_cache_key(HttpRequest())

    def test_allow_request_returns_true_if_key_is_none(self):
        throttle = SimpleRateThrottle()
        throttle.rate = "some rate"
        throttle.get_cache_key = lambda *args: None
        assert throttle.allow_request(request=HttpRequest()) is True

    def test_wait_returns_correct_waiting_time_without_history(self):
        throttle = SimpleRateThrottle()
        throttle.num_requests = 1
        throttle.duration = 60
        throttle.history = []
        waiting_time = throttle.wait()
        assert isinstance(waiting_time, float)
        assert waiting_time == 30.0

    def test_wait_returns_none_if_there_are_no_available_requests(self):
        throttle = SimpleRateThrottle()
        throttle.num_requests = 1
        throttle.duration = 60
        throttle.now = throttle.timer()
        throttle.history = [throttle.timer() for _ in range(3)]
        assert throttle.wait() is None


class TestUserRateThrottle:
    def setup_method(self):
        self.throttle = UserRateThrottle()
        self.request = HttpRequest()
        self.request.user = None

    @pytest.mark.django_db
    def test_get_cache_key_returns_correct_value_for_authenticated_request(self):
        user = User.objects.create(username="test")
        self.request.user = user
        assert self.throttle.get_cache_key(self.request) == "throttle_user_1"

    def test_get_cache_key_defaults_to_none(self):
        cache_key = self.throttle.get_cache_key(self.request)
        assert cache_key == "throttle_user_None"

    def test_get_cache_key_returns_correct_value(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "2.2.2.2"

        cache_key = self.throttle.get_cache_key(self.request)
        assert cache_key == "throttle_user_2.2.2.2"


class TestDynamicRateThrottle:
    def setup_method(self):
        self.request = HttpRequest()
        self.request.user = None

    def test_init_fails_without_scope(self):
        with pytest.raises(
            ImproperlyConfigured,
            match="You must set either `.scope` or `.rate` for 'DynamicRateThrottle' throttle",
        ):
            DynamicRateThrottle()

        with pytest.raises(
            ImproperlyConfigured,
            match="No default throttle rate set for 'some_scope' scope",
        ):
            DynamicRateThrottle(scope="some_scope")  # scope doesn't exist

    @pytest.mark.django_db
    def test_get_cache_key_returns_correct_value_for_authenticated_request(
        self, monkeypatch
    ):
        with monkeypatch.context() as m:
            m.setattr(settings, "THROTTLE_RATES", {"some_scope": "5/m"})
            throttle = DynamicRateThrottle(scope="some_scope")
            user = User.objects.create(username="test")
            self.request.user = user
            assert throttle.get_cache_key(self.request) == "throttle_some_scope_1"

    def test_get_cache_key_defaults_to_none(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(settings, "THROTTLE_RATES", {"some_scope": "5/m"})
            throttle = DynamicRateThrottle(scope="some_scope")
            assert throttle.get_cache_key(self.request) == "throttle_some_scope_None"

    def test_allow_request_returns_true_for_none_rate(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(settings, "THROTTLE_RATES", {"some_scope": None})
            throttle = DynamicRateThrottle(scope="some_scope")
            assert throttle.allow_request(self.request) is True

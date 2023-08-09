from contextlib import contextmanager

from django.core.cache import cache
from ninja.testing import TestClient

from ninja_extra import NinjaExtraAPI, throttle
from ninja_extra.conf import settings
from ninja_extra.throttling import DynamicRateThrottle


class Throttle(DynamicRateThrottle):
    THROTTLE_RATES = {"test_limit": "1/day"}
    TIMER_SECONDS = 0

    def timer(self):
        return self.TIMER_SECONDS


api = NinjaExtraAPI(urls_namespace="decorator_xxf")


@api.get("/throttling_xxf")
@throttle(Throttle, scope="test_limit")
def throttling_xxf(request):
    return "foo"


client = TestClient(api)


class XffTestingBase:
    def setup_method(self):
        cache.clear()
        self.meta = {
            "REMOTE_ADDR": "3.3.3.3",
            "HTTP_X_FORWARDED_FOR": "0.0.0.0, 1.1.1.1, 2.2.2.2",
        }

    @contextmanager
    def config_proxy(self, num_proxies):
        settings.NUM_PROXIES = num_proxies
        yield
        settings.NUM_PROXIES = None


class TestIdWithXffBasic(XffTestingBase):
    def test_accepts_request_under_limit(self):
        with self.config_proxy(0):
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200

    def test_denies_request_over_limit(self):
        with self.config_proxy(0):
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 429


class TestXffSpoofing(XffTestingBase):
    def test_xff_spoofing_doesnt_change_machine_id_with_one_app_proxy(self):
        with self.config_proxy(1):
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200
            self.meta.update({"HTTP_X_FORWARDED_FOR": "4.4.4.4, 5.5.5.5, 2.2.2.2"})
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 429

    def test_xff_spoofing_doesnt_change_machine_id_with_two_app_proxies(self):
        with self.config_proxy(2):
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200
            self.meta.update({"HTTP_X_FORWARDED_FOR": "4.4.4.4, 1.1.1.1, 2.2.2.2"})
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 429


class TestXffUniqueMachines(XffTestingBase):
    def test_unique_clients_are_counted_independently_with_one_proxy(self):
        with self.config_proxy(1):
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200
            self.meta.update({"HTTP_X_FORWARDED_FOR": "0.0.0.0, 1.1.1.1, 7.7.7.7"})
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200

    def test_unique_clients_are_counted_independently_with_two_proxies(self):
        with self.config_proxy(2):
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200
            self.meta.update({"HTTP_X_FORWARDED_FOR": "0.0.0.0, 7.7.7.7, 2.2.2.2"})
            response = client.get("/throttling_xxf", META=self.meta)
            assert response.status_code == 200

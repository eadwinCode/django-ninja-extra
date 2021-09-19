from injector import Injector

from ninja_extra.dependency_resolver import get_injector, service_resolver


class Service1:
    pass


class Service2:
    pass


def test_get_injector():
    injector = get_injector()
    assert isinstance(injector, Injector)


def test_service_resolver_returns_object_or_list_or_objects():
    service1 = service_resolver(Service1)
    assert isinstance(service1, Service1)

    service1, service2 = service_resolver(Service1, Service2)
    assert isinstance(service1, Service1)
    assert isinstance(service2, Service2)

from typing import Callable, Dict
from unittest.mock import Mock

from ninja.testing.client import NinjaClientBase, NinjaResponse

from ninja_extra import APIController, NinjaExtraAPI


class NinjaExtraClientBase(NinjaClientBase):
    def __init__(self, controller: APIController) -> None:
        api = NinjaExtraAPI()
        controller_ninja_router = controller.get_router()
        assert controller_ninja_router
        controller_ninja_router.set_api_instance(api)
        self._urls_cache = list(controller_ninja_router.urls_paths(""))
        super(NinjaExtraClientBase, self).__init__(api)


class TestClient(NinjaExtraClientBase):
    def _call(self, func: Callable, request: Mock, kwargs: Dict) -> "NinjaResponse":
        return NinjaResponse(func(request, **kwargs))


class TestAsyncClient(NinjaExtraClientBase):
    async def _call(self, func: Callable, request: Mock, kwargs: Dict) -> NinjaResponse:
        return NinjaResponse(await func(request, **kwargs))

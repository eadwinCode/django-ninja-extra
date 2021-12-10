from json import dumps as json_dumps
from typing import Any, Callable, Dict, Type, Union
from unittest.mock import Mock
from urllib.parse import urlencode

from ninja.testing.client import NinjaClientBase, NinjaResponse

from ninja_extra import ControllerBase, NinjaExtraAPI


class NinjaExtraClientBase(NinjaClientBase):
    def __init__(self, controller_class: Union[Type[ControllerBase], Type]) -> None:
        api = NinjaExtraAPI()
        assert hasattr(controller_class, "get_api_controller"), "Not a valid object"
        controller_ninja_api_controller = controller_class.get_api_controller()
        assert controller_ninja_api_controller
        controller_ninja_api_controller.set_api_instance(api)
        self._urls_cache = list(controller_ninja_api_controller.urls_paths(""))
        super(NinjaExtraClientBase, self).__init__(api)

    def request(
        self,
        method: str,
        path: str,
        data: Dict = {},
        json: Any = None,
        **request_params: Any,
    ) -> "NinjaResponse":
        if json is not None:
            request_params["body"] = json_dumps(json)
        if "query" in request_params and isinstance(request_params["query"], dict):
            query = request_params.pop("query")
            url_encode = urlencode(query)
            path = f"{path}?{url_encode}"
        func, request, kwargs = self._resolve(method, path, data, request_params)
        return self._call(func, request, kwargs)  # type: ignore


class TestClient(NinjaExtraClientBase):
    def _call(self, func: Callable, request: Mock, kwargs: Dict) -> "NinjaResponse":
        return NinjaResponse(func(request, **kwargs))


class TestAsyncClient(NinjaExtraClientBase):
    async def _call(self, func: Callable, request: Mock, kwargs: Dict) -> NinjaResponse:
        return NinjaResponse(await func(request, **kwargs))

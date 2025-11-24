from json import dumps as json_dumps
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union
from unittest.mock import Mock
from urllib.parse import urlencode

from django.urls import Resolver404
from ninja import NinjaAPI, Router
from ninja.responses import NinjaJSONEncoder
from ninja.testing.client import NinjaClientBase, NinjaResponse

from ninja_extra import ControllerBase, NinjaExtraAPI


class NinjaExtraClientBase(NinjaClientBase):
    def __init__(
        self, router_or_app: Union[NinjaAPI, Router, Type[ControllerBase]], **kw: Any
    ) -> None:
        if hasattr(router_or_app, "get_api_controller"):
            api = NinjaExtraAPI(**kw)
            controller_ninja_api_controller = router_or_app.get_api_controller()
            assert controller_ninja_api_controller
            controller_ninja_api_controller.set_api_instance(api)
            self._urls_cache = list(controller_ninja_api_controller.urls_paths(""))
            router_or_app = api
        super(NinjaExtraClientBase, self).__init__(router_or_app)

    def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        json: Any = None,
        **request_params: Any,
    ) -> "NinjaResponse":
        if json is not None:
            request_params["body"] = json_dumps(json, cls=NinjaJSONEncoder)
        if "query" in request_params and isinstance(request_params["query"], dict):
            query = request_params.pop("query")
            url_encode = urlencode(query)
            path = f"{path}?{url_encode}"
        func, request, kwargs = self._resolve(
            method, path, {} if data is None else data, request_params
        )
        return self._call(func, request, kwargs)  # type: ignore

    def _resolve(
        self, method: str, path: str, data: Dict, request_params: Any
    ) -> Tuple[Callable, Mock, Dict]:
        url_path = path.split("?")[0].lstrip("/")
        for url in self.urls:
            try:
                match = url.resolve(url_path)
            except Resolver404:
                continue
            if match:
                request = self._build_request(method, path, data, request_params)
                return match.func, request, match.kwargs
        raise Exception(f'Cannot resolve "{path}"')


class TestClient(NinjaExtraClientBase):
    def _call(self, func: Callable, request: Mock, kwargs: Dict) -> "NinjaResponse":
        return NinjaResponse(func(request, **kwargs))


class TestAsyncClient(NinjaExtraClientBase):
    async def _call(self, func: Callable, request: Mock, kwargs: Dict) -> NinjaResponse:
        return NinjaResponse(await func(request, **kwargs))

from django.http import HttpRequest
from django.http.response import HttpResponse
from ninja.operation import PathView as NinjaPathView


class PathView(NinjaPathView):
    async def _async_view(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # type: ignore
        return await super(PathView, self)._async_view(request, *args, **kwargs)

    def _sync_view(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # type: ignore
        return super(PathView, self)._sync_view(request, *args, **kwargs)

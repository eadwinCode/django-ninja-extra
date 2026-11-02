"""Regression tests for operation cloning.

django-ninja >= 1.6.0 clones operations when binding routers (BoundRouter),
and the base ``Operation.clone()`` recreates the instance without calling
``__init__`` (to skip expensive processing), copying only a fixed set of
attributes. ``ninja_extra`` adds its own ``is_coroutine`` attribute in
``__init__``, so the clone must re-copy it or ``_set_auth`` fails with
``AttributeError: 'AsyncOperation' object has no attribute 'is_coroutine'``.

See https://github.com/eadwinCode/django-ninja-extra/issues/352
"""

from ninja_extra import NinjaExtraAPI, api_controller, route
from ninja_extra.operation import AsyncOperation, Operation
from ninja_extra.security import AsyncHttpBearer


class _Bearer(AsyncHttpBearer):
    async def authenticate(self, request, token):
        return token if token == "secret" else None


def _first_operation(api):
    for bound_router in api._controller_routers:
        for path_view in bound_router.path_operations.values():
            for operation in path_view.operations:
                return operation
    raise AssertionError("no operation registered")


def test_async_operation_clone_preserves_is_coroutine(reflect_context):
    @api_controller("/clone-async", auth=_Bearer())
    class AsyncController:
        @route.get("/data")
        async def get_data(self):
            return {"ok": True}

    api = NinjaExtraAPI(urls_namespace="clone_async")
    api.register_controllers(AsyncController)

    operation = _first_operation(api)
    assert isinstance(operation, AsyncOperation)
    assert operation.is_coroutine is True

    cloned = operation.clone()
    # Regression for #352: the custom ``is_coroutine`` attribute must survive
    # cloning, even though the base ``clone()`` skips ``__init__``.
    assert cloned.is_coroutine == operation.is_coroutine


def test_sync_operation_clone_preserves_is_coroutine(reflect_context):
    @api_controller("/clone-sync")
    class SyncController:
        @route.get("/data")
        def get_data(self):
            return {"ok": True}

    api = NinjaExtraAPI(urls_namespace="clone_sync")
    api.register_controllers(SyncController)

    operation = _first_operation(api)
    assert isinstance(operation, Operation)
    assert operation.is_coroutine is False

    cloned = operation.clone()
    assert cloned.is_coroutine == operation.is_coroutine


def test_building_urls_with_async_controller_auth_does_not_raise(reflect_context):
    # The original #352 traceback crashed while Django built the URLconf
    # (api.urls -> _get_bound_routers -> _set_auth) for an async controller
    # with controller-level async auth.
    @api_controller("/urls-async", auth=_Bearer())
    class AsyncController:
        @route.get("/data")
        async def get_data(self):
            return {"ok": True}

    api = NinjaExtraAPI(urls_namespace="urls_async")
    api.register_controllers(AsyncController)

    # Must not raise AttributeError: 'AsyncOperation' object has no attribute 'is_coroutine'
    assert api.urls is not None

import pytest

from ninja_extra import APIController, NinjaExtraAPI, route, router


class RouterControllerExample(APIController):
    auto_import = False

    @route.get("/example")
    def example(self):
        pass


class TestControllerRouter:
    def test_controller_router_as_decorator(self):
        router_instance = router("prefix", tags=["new_tag"])

        @router_instance
        class RouterControllerDecorator(APIController):
            auto_import = False

        assert router_instance.prefix == "prefix"
        assert RouterControllerDecorator.get_router() == router_instance
        assert router_instance.controller == RouterControllerDecorator

        class RouterController(APIController):
            auto_import = False

        router_instance = router("prefix2", tags="new_tag", controller=RouterController)
        assert router_instance.controller == RouterController
        assert router_instance.prefix == "prefix2"
        assert router_instance.tags == ["new_tag"]
        assert RouterController.get_router() == router_instance
        assert router_instance.controller == RouterController

    def test_api_ninja_controller_registration(self):
        router_instance = router("prefix", tags=["new_tag"])
        ninja_extra_api = NinjaExtraAPI()

        @router_instance
        class RouterControllerDecorator(APIController):
            auto_import = False

        ninja_extra_api.add_controller_router(router_instance)
        with pytest.raises(Exception):
            ninja_extra_api.add_controller_router(dict())
        with pytest.raises(Exception):
            ninja_extra_api.add_controller_router(
                router("prefix/test", tags=["new_tag_test"])
            )

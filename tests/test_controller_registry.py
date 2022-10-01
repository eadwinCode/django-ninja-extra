from ninja_extra import ControllerBase, api_controller
from ninja_extra.controllers.registry import ControllerRegistry


@api_controller
class AutoImportFalseControllerSample(ControllerBase):
    auto_import = False


@api_controller
class AutoImportTrueControllerSample(ControllerBase):
    auto_import = True


def test_can_not_add_controller_for_auto_false():
    registry = ControllerRegistry()
    registry.clear_controller()
    registry.add_controller(AutoImportFalseControllerSample)
    assert str(AutoImportFalseControllerSample) not in registry.controllers


def test_can_add_controller_for_auto_true():
    registry = ControllerRegistry()
    registry.clear_controller()
    registry.add_controller(AutoImportTrueControllerSample)
    assert str(AutoImportTrueControllerSample) in registry.controllers


def test_remove_controller_works():
    registry = ControllerRegistry()
    registry.clear_controller()

    registry.add_controller(AutoImportTrueControllerSample)
    assert str(AutoImportTrueControllerSample) in registry.controllers
    result = registry.remove_controller(AutoImportTrueControllerSample)
    assert result
    assert str(AutoImportTrueControllerSample) not in registry.controllers
    assert registry.remove_controller(AutoImportTrueControllerSample) is None


def test_clear_registry_works():
    registry = ControllerRegistry()
    registry.add_controller(AutoImportTrueControllerSample)
    assert str(AutoImportTrueControllerSample) in registry.controllers
    registry.clear_controller()
    assert len(registry.controllers) == 0

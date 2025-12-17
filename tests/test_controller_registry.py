from ninja_extra import ControllerBase, api_controller
from ninja_extra.controllers.registry import ControllerRegistry


@api_controller
class AutoImportFalseControllerSample(ControllerBase):
    auto_import = False


@api_controller
class AutoImportTrueControllerSample(ControllerBase):
    auto_import = True


def test_can_not_add_controller_for_auto_false(reflect_context):
    registry = ControllerRegistry()
    registry.clear_controller()

    registry.add_controller(AutoImportFalseControllerSample)
    controllers = registry.get_controllers()

    assert str(AutoImportFalseControllerSample) not in controllers


def test_can_add_controller_for_auto_true(reflect_context):
    registry = ControllerRegistry()
    registry.clear_controller()

    registry.add_controller(AutoImportTrueControllerSample)

    controllers = registry.get_controllers()
    assert str(AutoImportTrueControllerSample) in controllers


def test_remove_controller_works(reflect_context):
    registry = ControllerRegistry()
    registry.clear_controller()

    registry.add_controller(AutoImportTrueControllerSample)
    controllers = registry.get_controllers()

    assert str(AutoImportTrueControllerSample) in controllers
    result = registry.remove_controller(AutoImportTrueControllerSample)

    assert result
    controllers = registry.get_controllers()

    assert str(AutoImportTrueControllerSample) not in controllers
    assert registry.remove_controller(AutoImportTrueControllerSample) is None


def test_clear_registry_works(reflect_context):
    registry = ControllerRegistry()
    registry.add_controller(AutoImportTrueControllerSample)

    controllers = registry.get_controllers()
    assert str(AutoImportTrueControllerSample) in controllers

    registry.clear_controller()
    controllers = registry.get_controllers()

    assert len(controllers) == 0

import warnings

import pytest


def test_route_context_deprecation():
    with pytest.warns(
        DeprecationWarning,
        match="RouteContext is deprecated and will be removed in a future version.",
    ):
        from ninja_extra.controllers import RouteContext

        assert RouteContext is not None  # Verify we can still access it


def test_no_warning_for_other_imports():
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # Turn warnings into errors
        from ninja_extra.controllers import ControllerBase  # This should not warn

        assert ControllerBase is not None

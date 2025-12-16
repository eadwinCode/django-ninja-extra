import warnings


def test_no_warning_for_other_imports():
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # Turn warnings into errors
        from ninja_extra.controllers import ControllerBase  # This should not warn

        assert ControllerBase is not None

import pytest

from ninja_extra import ModelEndpointFactory


def test_path_parameter_duplicate():
    with pytest.raises(ValueError):
        ModelEndpointFactory.delete(path="/{int:ex}/somewhere/{ex}", lookup_param="any")

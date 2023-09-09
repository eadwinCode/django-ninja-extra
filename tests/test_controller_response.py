import uuid

import pytest
from pydantic import BaseModel

from ninja_extra.controllers.response import (
    ControllerResponse,
    Detail,
    Id,
    Ok,
)


class ASchema(BaseModel):
    age: int


def test_controller_response_raise_type_error_for_base_model():
    with pytest.raises(RuntimeError):
        ControllerResponse()


def test_ok_normal_response_model():
    with pytest.raises(RuntimeError):
        Ok("this is normal response")


def test_ok_generic_response_model():
    with pytest.raises(RuntimeError):
        Ok[ASchema]


def test_id_normal_response_model():
    with pytest.raises(RuntimeError):
        Id(852)


def test_id_generic_response_model():
    with pytest.raises(RuntimeError):
        Id[uuid.UUID]


def test_details_normal_response_response_model():
    with pytest.raises(RuntimeError):
        Detail("this is normal response", 500)


def test_details_generic_response_response_model():
    with pytest.raises(RuntimeError):
        Detail[ASchema]

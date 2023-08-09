import sys
import uuid

import pytest
from pydantic import BaseModel

from ninja_extra.controllers.response import (
    ControllerResponse,
    ControllerResponseMeta,
    Detail,
    Id,
    Ok,
)


class ASchema(BaseModel):
    age: int


def test_controller_response_raise_type_error_for_base_model():
    with pytest.raises(TypeError):
        ControllerResponse()


def test_ok_normal_response_model():
    ok_any = Ok("this is normal response")
    assert ok_any.convert_to_schema().dict() == {"detail": "this is normal response"}
    assert ok_any.status_code == 200
    assert type(Ok) == ControllerResponseMeta


def test_ok_generic_response_model():
    ok_a_schema = Ok[ASchema]
    ok_a_schema_instance = ok_a_schema({"age": 34})
    assert "ASchema" in ok_a_schema_instance.get_schema().__name__
    assert ok_a_schema_instance.convert_to_schema().dict() == {"detail": {"age": 34}}
    assert ok_a_schema_instance.status_code == 200
    assert ok_a_schema == Ok[ASchema]
    type(ok_a_schema)
    assert type(ok_a_schema) == ControllerResponseMeta


def test_id_normal_response_model():
    id_any = Id(852)
    assert id_any.convert_to_schema().dict() == {"id": 852}
    assert id_any.status_code == 201
    assert type(Id) == ControllerResponseMeta


def test_id_generic_response_model():
    id_uuid = Id[uuid.UUID]
    uuid_value = uuid.uuid4()
    id_uuid_instance = id_uuid(uuid_value)
    assert "UUID" in id_uuid_instance.get_schema().__name__
    assert id_uuid_instance.convert_to_schema().dict() == {"id": uuid_value}
    assert id_uuid_instance.status_code == 201
    assert id_uuid == Id[uuid.UUID]
    assert type(id_uuid) == ControllerResponseMeta


def test_details_normal_response_response_model():
    detail_any = Detail("this is normal response", 500)
    assert detail_any.convert_to_schema().dict() == {
        "detail": "this is normal response"
    }
    assert detail_any.status_code == 500
    assert type(Detail) == ControllerResponseMeta


def test_details_generic_response_response_model():
    details_a_schema = Detail[ASchema]
    detail_a_schema_instance = details_a_schema({"age": 34}, 400)
    assert "ASchema" in detail_a_schema_instance.get_schema().__name__
    assert detail_a_schema_instance.convert_to_schema().dict() == {
        "detail": {"age": 34}
    }
    assert detail_a_schema_instance.status_code == 400
    assert details_a_schema == Detail[ASchema]
    assert type(details_a_schema) == ControllerResponseMeta


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python >= 3.7")
def test_generic_schema_with_k_t_fails():
    with pytest.raises(TypeError, match="Tuple Generic Model not supported"):
        Detail[ASchema, ASchema]

import pytest
from .main import QueryParamController

from ninja_extra.testing import TestClient

response_missing = {
    "detail": [
        {
            "type": "missing",
            "loc": ["query", "query"],
            "msg": "Field required",
        }
    ]
}

response_not_valid_int = {
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["query", "query"],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
        }
    ]
}

response_not_valid_int_float = {
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["query", "query"],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
        }
    ]
}


client = TestClient(QueryParamController)


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/", 422, response_missing),
        ("/?query=baz", 200, "foo bar baz"),
        ("/?not_declared=baz", 422, response_missing),
        ("/optional", 200, "foo bar"),
        ("/optional?query=baz", 200, "foo bar baz"),
        ("/optional?not_declared=baz", 200, "foo bar"),
        ("/int", 422, response_missing),
        ("/int?query=42", 200, "foo bar 42"),
        ("/int?query=42.5", 422, response_not_valid_int_float),
        ("/int?query=baz", 422, response_not_valid_int),
        ("/int?not_declared=baz", 422, response_missing),
        ("/int/optional", 200, "foo bar"),
        ("/int/optional?query=50", 200, "foo bar 50"),
        ("/int/optional?query=foo", 422, response_not_valid_int),
        ("/int/default", 200, "foo bar 10"),
        ("/int/default?query=50", 200, "foo bar 50"),
        ("/int/default?query=foo", 422, response_not_valid_int),
        ("/list?query=a&query=b&query=c", 200, "a,b,c"),
        ("/list-optional?query=a&query=b&query=c", 200, "a,b,c"),
        ("/list-optional?query=a", 200, "a"),
        ("/list-optional", 200, None),
        ("/param", 200, "foo bar"),
        ("/param?query=50", 200, "foo bar 50"),
        ("/param-required", 422, response_missing),
        ("/param-required?query=50", 200, "foo bar 50"),
        ("/param-required/int", 422, response_missing),
        ("/param-required/int?query=50", 200, "foo bar 50"),
        ("/param-required/int?query=foo", 422, response_not_valid_int),
        ("/aliased-name?aliased.-_~name=foo", 200, "foo bar foo"),
    ],
)
def test_get_path(path, expected_status, expected_response):
    response = client.get(path)
    resp = response.json()
    print(resp)
    assert response.status_code == expected_status
    assert resp == expected_response

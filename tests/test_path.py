import pytest

from ninja_extra.testing import TestClient

from .main import PathParamController

client = TestClient(PathParamController)


def test_text_get():
    response = client.get("/text")
    assert response.status_code == 200, response.text
    assert response.json() == "Hello World"


response_not_valid_bool = {
    "detail": [
        {
            "type": "bool_parsing",
            "loc": ["path", "item_id"],
            "msg": "Input should be a valid boolean, unable to interpret input",
        }
    ]
}

response_not_valid_int = {
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["path", "item_id"],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
        }
    ]
}

response_not_valid_int_float = {
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["path", "item_id"],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
        }
    ]
}

response_not_valid_float = {
    "detail": [
        {
            "type": "float_parsing",
            "loc": ["path", "item_id"],
            "msg": "Input should be a valid number, unable to parse string as a number",
        }
    ]
}

response_at_least_3 = {
    "detail": [
        {
            "type": "string_too_short",
            "loc": ["path", "item_id"],
            "msg": "String should have at least 3 characters",
            "ctx": {"min_length": 3},
        }
    ]
}


response_at_least_2 = {
    "detail": [
        {
            "type": "string_too_short",
            "loc": ["path", "item_id"],
            "msg": "String should have at least 2 characters",
            "ctx": {"min_length": 2},
        }
    ]
}


response_maximum_3 = {
    "detail": [
        {
            "type": "string_too_long",
            "loc": ["path", "item_id"],
            "msg": "String should have at most 3 characters",
            "ctx": {"max_length": 3},
        }
    ]
}


response_greater_than_3 = {
    "detail": [
        {
            "type": "greater_than",
            "loc": ["path", "item_id"],
            "msg": "Input should be greater than 3",
            "ctx": {"gt": 3.0},
        }
    ]
}


response_greater_than_0 = {
    "detail": [
        {
            "type": "greater_than",
            "loc": ["path", "item_id"],
            "msg": "Input should be greater than 0",
            "ctx": {"gt": 0.0},
        }
    ]
}


response_greater_than_1 = {
    "detail": [
        {
            "type": "greater_than",
            "loc": ["path", "item_id"],
            "msg": "Input should be greater than 1",
            "ctx": {"gt": 1},
        }
    ]
}


response_greater_than_equal_3 = {
    "detail": [
        {
            "type": "greater_than_equal",
            "loc": ["path", "item_id"],
            "msg": "Input should be greater than or equal to 3",
            "ctx": {"ge": 3.0},
        }
    ]
}


response_less_than_3 = {
    "detail": [
        {
            "type": "less_than",
            "loc": ["path", "item_id"],
            "msg": "Input should be less than 3",
            "ctx": {"lt": 3.0},
        }
    ]
}


response_less_than_0 = {
    "detail": [
        {
            "type": "less_than",
            "loc": ["path", "item_id"],
            "msg": "Input should be less than 0",
            "ctx": {"lt": 0.0},
        }
    ]
}

response_less_than_equal_3 = {
    "detail": [
        {
            "type": "less_than_equal",
            "loc": ["path", "item_id"],
            "msg": "Input should be less than or equal to 3",
            "ctx": {"le": 3.0},
        }
    ]
}


response_not_valid_pattern = {
    "detail": [
        {
            "ctx": {
                "pattern": "^foo",
            },
            "loc": ["path", "item_id"],
            "msg": "String should match pattern '^foo'",
            "type": "string_pattern_mismatch",
        }
    ]
}


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/foobar", 200, "foobar"),
        ("/str/foobar", 200, "foobar"),
        ("/str/42", 200, "42"),
        ("/str/True", 200, "True"),
        ("/int/foobar", 422, response_not_valid_int),
        ("/int/True", 422, response_not_valid_int),
        ("/int/42", 200, 42),
        ("/int/42.5", 422, response_not_valid_int_float),
        ("/float/foobar", 422, response_not_valid_float),
        ("/float/True", 422, response_not_valid_float),
        ("/float/42", 200, 42),
        ("/float/42.5", 200, 42.5),
        ("/bool/foobar", 422, response_not_valid_bool),
        ("/bool/True", 200, True),
        ("/bool/42", 422, response_not_valid_bool),
        ("/bool/42.5", 422, response_not_valid_bool),
        ("/bool/1", 200, True),
        ("/bool/0", 200, False),
        ("/bool/true", 200, True),
        ("/bool/False", 200, False),
        ("/bool/false", 200, False),
        ("/param/foo", 200, "foo"),
        ("/param-required/foo", 200, "foo"),
        ("/param-minlength/foo", 200, "foo"),
        ("/param-minlength/fo", 422, response_at_least_3),
        ("/param-maxlength/foo", 200, "foo"),
        ("/param-maxlength/foobar", 422, response_maximum_3),
        ("/param-min_maxlength/foo", 200, "foo"),
        ("/param-min_maxlength/foobar", 422, response_maximum_3),
        ("/param-min_maxlength/f", 422, response_at_least_2),
        ("/param-gt/42", 200, 42),
        ("/param-gt/2", 422, response_greater_than_3),
        ("/param-gt0/0.05", 200, 0.05),
        ("/param-gt0/0", 422, response_greater_than_0),
        ("/param-ge/42", 200, 42),
        ("/param-ge/3", 200, 3),
        ("/param-ge/2", 422, response_greater_than_equal_3),
        ("/param-lt/42", 422, response_less_than_3),
        ("/param-lt/2", 200, 2),
        ("/param-lt0/-1", 200, -1),
        ("/param-lt0/0", 422, response_less_than_0),
        ("/param-le/42", 422, response_less_than_equal_3),
        ("/param-le/3", 200, 3),
        ("/param-le/2", 200, 2),
        ("/param-lt-gt/2", 200, 2),
        ("/param-lt-gt/4", 422, response_less_than_3),
        ("/param-lt-gt/0", 422, response_greater_than_1),
        ("/param-le-ge/2", 200, 2),
        ("/param-le-ge/1", 200, 1),
        ("/param-le-ge/3", 200, 3),
        ("/param-le-ge/4", 422, response_less_than_equal_3),
        ("/param-lt-int/2", 200, 2),
        ("/param-lt-int/42", 422, response_less_than_3),
        ("/param-lt-int/2.7", 422, response_not_valid_int_float),
        ("/param-gt-int/42", 200, 42),
        ("/param-gt-int/2", 422, response_greater_than_3),
        ("/param-gt-int/2.7", 422, response_not_valid_int_float),
        ("/param-le-int/42", 422, response_less_than_equal_3),
        ("/param-le-int/3", 200, 3),
        ("/param-le-int/2", 200, 2),
        ("/param-le-int/2.7", 422, response_not_valid_int_float),
        ("/param-ge-int/42", 200, 42),
        ("/param-ge-int/3", 200, 3),
        ("/param-ge-int/2", 422, response_greater_than_equal_3),
        ("/param-ge-int/2.7", 422, response_not_valid_int_float),
        ("/param-lt-gt-int/2", 200, 2),
        ("/param-lt-gt-int/4", 422, response_less_than_3),
        ("/param-lt-gt-int/0", 422, response_greater_than_1),
        ("/param-lt-gt-int/2.7", 422, response_not_valid_int_float),
        ("/param-le-ge-int/2", 200, 2),
        ("/param-le-ge-int/1", 200, 1),
        ("/param-le-ge-int/3", 200, 3),
        ("/param-le-ge-int/4", 422, response_less_than_equal_3),
        ("/param-le-ge-int/2.7", 422, response_not_valid_int_float),
        ("/param-pattern/foo", 200, "foo"),
        ("/param-pattern/fo", 422, response_not_valid_pattern),
    ],
)
def test_get_path(path, expected_status, expected_response):
    response = client.get(path)
    print(path, response.json())
    assert response.status_code == expected_status
    assert response.json() == expected_response


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/param-django-str/42", 200, "42"),
        ("/param-django-str/-1", 200, "-1"),
        ("/param-django-str/foobar", 200, "foobar"),
        ("/param-django-int/0", 200, 0),
        ("/param-django-int/42", 200, 42),
        ("/param-django-int/42.5", "Cannot resolve", Exception),
        ("/param-django-int/-1", "Cannot resolve", Exception),
        ("/param-django-int/True", "Cannot resolve", Exception),
        ("/param-django-int/foobar", "Cannot resolve", Exception),
        ("/param-django-int/not-an-int", 200, "Found not-an-int"),
        # ("/path/param-django-int-str/42", 200, "42"), # https://github.com/pydantic/pydantic/issues/5993
        ("/param-django-int-str/42.5", "Cannot resolve", Exception),
        (
            "/param-django-slug/django-ninja-is-the-best",
            200,
            "django-ninja-is-the-best",
        ),
        ("/param-django-slug/42.5", "Cannot resolve", Exception),
        (
            "/param-django-uuid/31ea378c-c052-4b4c-bf0b-679ce5cfcc2a",
            200,
            "31ea378c-c052-4b4c-bf0b-679ce5cfcc2a",
        ),
        (
            "/param-django-uuid/31ea378c-c052-4b4c-bf0b-679ce5cfcc2",
            "Cannot resolve",
            Exception,
        ),
        (
            "/param-django-uuid-str/31ea378c-c052-4b4c-bf0b-679ce5cfcc2a",
            200,
            "31ea378c-c052-4b4c-bf0b-679ce5cfcc2a",
        ),
        ("/param-django-path/some/path/things/after", 200, "some/path/things"),
        ("/param-django-path/less/path/after", 200, "less/path"),
        ("/param-django-path/plugh/after", 200, "plugh"),
        ("/param-django-path//after", "Cannot resolve", Exception),
        ("/param-django-custom-int/42", 200, 24),
        ("/param-django-custom-int/x42", "Cannot resolve", Exception),
        ("/param-django-custom-float/42", 200, 0.24),
        ("/param-django-custom-float/x42", "Cannot resolve", Exception),
    ],
)
def test_get_path_django(path, expected_status, expected_response):
    if expected_response is Exception:
        with pytest.raises(Exception, match=expected_status):
            client.get(path)
    else:
        response = client.get(path)
        print(response.json())
        assert response.status_code == expected_status
        assert response.json() == expected_response

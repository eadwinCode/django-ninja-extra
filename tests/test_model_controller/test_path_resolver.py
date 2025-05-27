from unittest.mock import MagicMock, patch

import pytest
from pydantic import UUID4

from ninja_extra.controllers.model.path_resolver import (
    AsyncPathResolverOperation,
    PathCompiledResult,
    PathResolverOperation,
    compile_path,
)


def test_get_path_fields_with_compiled_path():
    # Create PathResolverOperation with just enough attributes for testing get_path_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={"id": int, "name": str}, query_parameters={}
    )
    resolver.prefix_route_params = None

    # Call get_path_fields and convert generator to dict
    path_fields = dict(resolver.get_path_fields())

    # Verify results
    assert "id" in path_fields
    assert "name" in path_fields
    assert path_fields["id"][0] is int
    assert path_fields["name"][0] is str
    # Verify the second item in the tuple is ... (Ellipsis)
    assert path_fields["id"][1] is ...
    assert path_fields["name"][1] is ...


def test_get_path_fields_with_prefix_route_params():
    # Create PathResolverOperation with just enough attributes for testing get_path_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={}, query_parameters={}
    )
    resolver.prefix_route_params = {"org_id": "int", "username": "str"}

    # Call get_path_fields and convert generator to dict
    path_fields = dict(resolver.get_path_fields())

    # Verify results
    assert "org_id" in path_fields
    assert "username" in path_fields
    assert path_fields["org_id"][0] is int
    assert path_fields["username"][0] is str
    # Verify the second item in the tuple is ... (Ellipsis)
    assert path_fields["org_id"][1] is ...
    assert path_fields["username"][1] is ...


def test_get_path_fields_with_both():
    # Create PathResolverOperation with just enough attributes for testing get_path_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={"id": int}, query_parameters={}
    )
    resolver.prefix_route_params = {"org_id": "uuid"}

    # Call get_path_fields and convert generator to dict
    path_fields = dict(resolver.get_path_fields())

    # Verify results
    assert "id" in path_fields
    assert "org_id" in path_fields
    assert path_fields["id"][0] is int
    assert path_fields["org_id"][0] == UUID4  # uuid maps to UUID4 in STRING_TYPES


def test_get_path_fields_with_invalid_type():
    # Create PathResolverOperation with just enough attributes for testing get_path_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={}, query_parameters={}
    )
    resolver.prefix_route_params = {
        "param": "invalid_type"  # This type is not in STRING_TYPES
    }

    # Verify ValueError is raised with the correct message
    with pytest.raises(
        ValueError, match=r"Unknown path type 'invalid_type' for parameter 'param'"
    ):
        dict(resolver.get_path_fields())


def test_get_path_fields_empty():
    # Create PathResolverOperation with just enough attributes for testing get_path_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={}, query_parameters={}
    )
    resolver.prefix_route_params = None

    # Should yield nothing
    path_fields = list(resolver.get_path_fields())
    assert len(path_fields) == 0


def test_get_path_fields_case_insensitive():
    # Create PathResolverOperation with just enough attributes for testing get_path_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={}, query_parameters={}
    )
    resolver.prefix_route_params = {
        "id": "INT",  # uppercase, should be converted to lowercase
        "name": "Str",  # mixed case, should be converted to lowercase
    }

    # Call get_path_fields and convert generator to dict
    path_fields = dict(resolver.get_path_fields())

    # Verify results
    assert path_fields["id"][0] is int
    assert path_fields["name"][0] is str


def test_compile_path_with_path_params():
    path = "/{int:id}/{str:name}"
    result = compile_path(path)

    assert "id" in result.param_convertors
    assert "name" in result.param_convertors
    assert result.param_convertors["id"] is int
    assert result.param_convertors["name"] is str
    assert not result.query_parameters


def test_compile_path_with_query_params():
    path = "/users?id=int&name=str"
    result = compile_path(path)

    assert not result.param_convertors
    assert "id" in result.query_parameters
    assert "name" in result.query_parameters
    assert result.query_parameters["id"] == ["int"]
    assert result.query_parameters["name"] == ["str"]


def test_compile_path_with_both_params():
    path = "/{int:id}/users/{uuid:user_id}?filter=str&page=int"
    result = compile_path(path)

    assert "id" in result.param_convertors
    assert "user_id" in result.param_convertors
    assert result.param_convertors["id"] is int
    assert result.param_convertors["user_id"] == UUID4

    assert "filter" in result.query_parameters
    assert "page" in result.query_parameters
    assert result.query_parameters["filter"] == ["str"]
    assert result.query_parameters["page"] == ["int"]


def test_compile_path_with_duplicated_params():
    path = "/{int:id}/{str:id}"

    with pytest.raises(
        ValueError, match=r"Duplicated param name id at path /{int:id}/{str:id}"
    ):
        compile_path(path)


def test_has_any_parameter_true():
    # With path parameters
    result1 = PathCompiledResult({"id": int}, {})
    assert result1.has_any_parameter() is True

    # With query parameters
    result2 = PathCompiledResult({}, {"q": ["str"]})
    assert result2.has_any_parameter() is True

    # With both
    result3 = PathCompiledResult({"id": int}, {"q": ["str"]})
    assert result3.has_any_parameter() is True


def test_has_any_parameter_false():
    result = PathCompiledResult({}, {})
    assert result.has_any_parameter() is False


def test_get_query_fields_with_query_params():
    # Create PathResolverOperation with just enough attributes for testing get_query_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={}, query_parameters={"page": ["int"], "search": ["str"]}
    )

    # Call get_query_fields and convert generator to dict
    query_fields = dict(resolver.get_query_fields())

    # Verify results
    assert "page" in query_fields
    assert "search" in query_fields
    assert query_fields["page"][0] is int
    assert query_fields["search"][0] is str
    # Verify the second item in the tuple is ... (Ellipsis)
    assert query_fields["page"][1] is ...
    assert query_fields["search"][1] is ...


def test_get_query_fields_empty():
    # Create PathResolverOperation with just enough attributes for testing get_query_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={}, query_parameters={}
    )

    # Should yield nothing
    query_fields = list(resolver.get_query_fields())
    assert len(query_fields) == 0


def test_get_query_fields_with_multiple_types():
    # Create PathResolverOperation with just enough attributes for testing get_query_fields
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver.compiled_path = PathCompiledResult(
        param_convertors={},
        # Multiple types, but only the first one should be used
        query_parameters={"filter": ["int", "str"]},
    )

    # Call get_query_fields and convert generator to dict
    query_fields = dict(resolver.get_query_fields())

    # Verify results
    assert "filter" in query_fields
    assert query_fields["filter"][0] is int  # Should use the first type


@patch("ninja_extra.controllers.model.path_resolver.add_ninja_contribute_args")
def test_path_resolver_view_function(mock_add_ninja):
    # Setup
    def example_view(request, user_id=None, page=None):
        return {"user_id": user_id, "page": page}

    # Create a PathResolverOperation with path parameters
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver._view_func = example_view
    resolver.path_construct_name = "PathModel123"
    resolver.query_construct_name = "QueryModel123"

    # Get the view function
    view_func = resolver.get_view_function()

    # Create a mock instance with a dict method
    path_model_instance = MagicMock()
    path_model_instance.dict.return_value = {"user_id": 123}

    query_model_instance = MagicMock()
    query_model_instance.dict.return_value = {"page": 1}

    # Call the view function with the mock instance
    result = view_func(
        "request_obj",
        PathModel123=path_model_instance,
        QueryModel123=query_model_instance,
    )

    # Assert results
    assert result == {"user_id": 123, "page": 1}
    path_model_instance.dict.assert_called_once()
    query_model_instance.dict.assert_called_once()


@patch("ninja_extra.controllers.model.path_resolver.add_ninja_contribute_args")
def test_path_resolver_view_function_no_models(mock_add_ninja):
    # Setup
    def example_view(request):
        return {"message": "Hello World"}

    # Create a PathResolverOperation with no path parameters
    resolver = PathResolverOperation.__new__(PathResolverOperation)
    resolver._view_func = example_view
    resolver.path_construct_name = "PathModel456"
    resolver.query_construct_name = "QueryModel456"

    # Get the view function
    view_func = resolver.get_view_function()

    # Call the view function without any models
    result = view_func("request_obj")

    # Assert results
    assert result == {"message": "Hello World"}


@patch("ninja_extra.controllers.model.path_resolver.add_ninja_contribute_args")
@pytest.mark.asyncio
async def test_async_path_resolver_view_function(mock_add_ninja):
    # Setup
    async def example_async_view(request, user_id=None, page=None):
        return {"user_id": user_id, "page": page}

    # Create an AsyncPathResolverOperation with path parameters
    resolver = AsyncPathResolverOperation.__new__(AsyncPathResolverOperation)
    resolver._view_func = example_async_view
    resolver.path_construct_name = "PathModel789"
    resolver.query_construct_name = "QueryModel789"

    # Get the view function
    view_func = resolver.get_view_function()

    # Create a mock instance with a dict method
    path_model_instance = MagicMock()
    path_model_instance.dict.return_value = {"user_id": 456}

    query_model_instance = MagicMock()
    query_model_instance.dict.return_value = {"page": 2}

    # Call the view function with the mock instance
    result = await view_func(
        "request_obj",
        PathModel789=path_model_instance,
        QueryModel789=query_model_instance,
    )

    # Assert results
    assert result == {"user_id": 456, "page": 2}
    path_model_instance.dict.assert_called_once()
    query_model_instance.dict.assert_called_once()

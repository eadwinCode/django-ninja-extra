import datetime
import functools
import re
import typing as t
import uuid
from urllib.parse import parse_qs, urlparse

from ninja import Query, Schema
from ninja.params import Path
from pydantic import UUID4, create_model

from ninja_extra.shortcuts import add_ninja_contribute_args

# Match parameters in URL paths, eg. '{param}', and '{int:param}'
PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*:)?([a-zA-Z_][a-zA-Z0-9_]*)}")


class PathCompiledResult(t.NamedTuple):
    param_convertors: t.Dict[str, t.Any]
    query_parameters: t.Dict[str, t.Any]

    def has_any_parameter(self) -> bool:
        return len(self.param_convertors) > 0 or len(self.query_parameters) > 0


STRING_TYPES: t.Dict[str, t.Type] = {
    "int": int,
    "path": str,
    "slug": str,
    "str": str,
    "uuid": UUID4,
    "datetime": datetime.datetime,
    "date": datetime.date,
}


def compile_path(path: str) -> PathCompiledResult:
    """
    Given a path string, like: "/{str:username}"

    regex:      "/(?P<username>[^/]+)"
    format:     "/{username}"
    convertors: {str:"username"}
    """
    duplicated_params = set()
    param_convertors = {}

    parsed_url = urlparse(path)
    query_parameters = parse_qs(parsed_url.query)

    for match in PARAM_REGEX.finditer(path):
        convertor_type, param_name = match.groups("str")
        convertor = convertor_type.rstrip(":")

        if param_name in param_convertors:
            duplicated_params.add(param_name)

        param_convertors[param_name] = STRING_TYPES[convertor.lower()]

    if duplicated_params:
        names = ", ".join(sorted(duplicated_params))
        ending = "s" if len(duplicated_params) > 1 else ""
        raise ValueError(f"Duplicated param name{ending} {names} at path {path}")

    return PathCompiledResult(param_convertors, query_parameters)


class PathResolverOperation:
    """
    Create a decorator to parse `path` parameters and resolve them during endpoint.
    For example:
    path=/{int:id}/tags/{post_id}?query=int&query1=int
    this will create two path parameters `id` and `post_id` and two query parameters `query` and `query1`
    for the decorated endpoint
    """

    def __init__(self, path: str, func: t.Callable) -> None:
        self.compiled_path = compile_path(path)
        self._view_func = func

        if self.compiled_path.has_any_parameter():
            _ninja_contribute_args: t.List[t.Tuple] = getattr(
                func, "_ninja_contribute_args", []
            )

            unique_key = str(uuid.uuid4().hex)[:5]

            self.path_construct_name = f"PathModel{unique_key}"
            self.query_construct_name = f"QueryModel{unique_key}"

            path_fields = dict(self.get_path_fields())
            query_fields = dict(self.get_query_fields())

            if path_fields:
                dynamic_path_model = create_model(
                    self.path_construct_name, __base__=Schema, **path_fields
                )
                add_ninja_contribute_args(
                    func,
                    (self.path_construct_name, dynamic_path_model, Path(...)),
                )

            if query_fields:
                dynamic_query_model = create_model(
                    self.query_construct_name, __base__=Schema, **query_fields
                )

                add_ninja_contribute_args(
                    func,
                    (self.query_construct_name, dynamic_query_model, Query(...)),
                )
            self.as_view = functools.wraps(func)(self.get_view_function())
        else:
            self.as_view = func  # type:ignore[assignment]

    def get_path_fields(self) -> t.Generator:
        for path_name, path_type in self.compiled_path.param_convertors.items():
            yield path_name, (path_type, ...)

    def get_query_fields(self) -> t.Generator:
        for path_name, path_type in self.compiled_path.query_parameters.items():
            path_type.append("str")
            yield path_name, (STRING_TYPES[path_type[0]], ...)

    def get_view_function(self) -> t.Callable:
        def as_view(*args: t.Any, **kwargs: t.Any) -> t.Any:
            func_kwargs = dict(kwargs)

            if self.path_construct_name in func_kwargs:
                dynamic_model_path_instance = func_kwargs.pop(self.path_construct_name)
                func_kwargs.update(dynamic_model_path_instance.dict())

            if self.query_construct_name in func_kwargs:
                dynamic_model_query_instance = func_kwargs.pop(
                    self.query_construct_name
                )
                func_kwargs.update(dynamic_model_query_instance.dict())

            return self._view_func(*args, **func_kwargs)

        return as_view


class AsyncPathResolverOperation(PathResolverOperation):
    def get_view_function(self) -> t.Callable:
        async def as_view(*args: t.Any, **kwargs: t.Any) -> t.Any:
            func_kwargs = dict(kwargs)

            if self.path_construct_name in func_kwargs:
                dynamic_model_path_instance = func_kwargs.pop(self.path_construct_name)
                func_kwargs.update(dynamic_model_path_instance.dict())

            if self.query_construct_name in func_kwargs:
                dynamic_model_query_instance = func_kwargs.pop(
                    self.query_construct_name
                )
                func_kwargs.update(dynamic_model_query_instance.dict())

            return await self._view_func(*args, **func_kwargs)

        return as_view

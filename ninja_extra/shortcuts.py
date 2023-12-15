from typing import Any, List, Optional, Tuple, Type, Union, cast, no_type_check

from django.db.models import Model, QuerySet
from ninja.types import DictStrAny, TCallable

from .exceptions import APIException, NotFound


@no_type_check
def add_ninja_contribute_args(func: TCallable, value: Tuple) -> None:
    _ninja_contribute_args: List[Tuple] = getattr(func, "_ninja_contribute_args", [])
    assert isinstance(_ninja_contribute_args, list)
    _ninja_contribute_args.append(value)
    func._ninja_contribute_args = _ninja_contribute_args


@no_type_check
def fail_silently(func: TCallable, *args: Any, **kwargs: Any) -> Optional[Any]:
    try:
        return func(*args, **kwargs)
    except Exception:
        pass
    return None


@no_type_check
def _get_queryset(klass: Type[Model]) -> QuerySet:
    # If it is a model class or anything else with ._default_manager
    if hasattr(klass, "_default_manager"):
        return cast(QuerySet, klass._default_manager.all())
    return cast(QuerySet, klass)


@no_type_check
def get_object_or_exception(
    klass: Union[Type[Model], QuerySet],
    error_message: str = None,
    exception: Type[APIException] = NotFound,
    **kwargs: Any,
) -> Any:
    queryset = _get_queryset(klass)
    _validate_queryset(klass, queryset)
    try:
        return queryset.get(**kwargs)
    except queryset.model.DoesNotExist as ex:
        if error_message:
            message = error_message
        else:
            message = "{} with {} was not found".format(
                queryset.model._meta.object_name, _format_dict(kwargs)
            )
        raise exception(detail=message) from ex


def _format_dict(table: DictStrAny) -> str:
    table_str = ""
    for k, v in table.items():
        table_str += "{} = {} ".format(str(k), str(v))
    return table_str


@no_type_check
def get_object_or_none(
    klass: Union[Type[Model], QuerySet], **kwargs: Any
) -> Optional[Any]:
    queryset = _get_queryset(klass)
    _validate_queryset(klass, queryset)
    try:
        return queryset.get(**kwargs)
    except (queryset.model.DoesNotExist, KeyError):
        return None


@no_type_check
def _validate_queryset(klass: Type[Model], queryset: Any) -> None:
    if not hasattr(queryset, "get"):
        klass__name = (
            klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        )
        raise ValueError(
            "First argument must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )

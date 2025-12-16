import functools
import inspect
import logging
import typing as t

logger = logging.getLogger("ellar")


def ensure_target(target: t.Union[t.Type, t.Callable]) -> t.Union[t.Type, t.Callable]:
    """
    Ensure the target is a class or a function, unwrapping methods to their underlying functions.

    :param target: The target object (class, function, or method).
    :return: The class or function.
    """
    res = target
    if inspect.ismethod(res):
        res = res.__func__
    return res


def is_decorated_with_partial(func_or_class: t.Any) -> bool:
    """
    Check if the object is decorated with `functools.partial`.

    :param func_or_class: The object to check.
    :return: True if decorated with partial, False otherwise.
    """
    return isinstance(func_or_class, functools.partial)


def is_decorated_with_wraps(func_or_class: t.Any) -> bool:
    """
    Check if the object is decorated with `functools.wraps`.

    :param func_or_class: The object to check.
    :return: True if decorated with wraps, False otherwise.
    """
    return hasattr(func_or_class, "__wrapped__")


def get_original_target(func_or_class: t.Any) -> t.Any:
    """
    Unwrap the object to find the original target, getting past partials and wraps.

    :param func_or_class: The object to unwrap.
    :return: The original underlying object.
    """
    while True:
        if is_decorated_with_partial(func_or_class):
            func_or_class = func_or_class.func
        elif is_decorated_with_wraps(func_or_class):
            func_or_class = func_or_class.__wrapped__
        else:
            return func_or_class


def transfer_metadata(
    old_target: t.Any, new_target: t.Any, clean_up: bool = False
) -> None:
    """
    Transfer metadata from one target to another.

    :param old_target: The source target.
    :param new_target: The destination target.
    :param clean_up: If True, delete metadata from the old target after transfer.
    """
    from ._reflect import reflect

    meta = reflect.get_all_metadata(old_target)
    for k, v in meta.items():
        reflect.define_metadata(k, v, new_target)

    if clean_up:
        reflect.delete_all_metadata(old_target)


@t.no_type_check
def fail_silently(func: t.Callable, *args: t.Any, **kwargs: t.Any) -> t.Optional[t.Any]:
    """
    Execute a function and return None if an exception occurs, logging the error blindly.

    :param func: The function to execute.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: The result of the function or None if an exception occurred.
    """
    try:
        return func(*args, **kwargs)
    except Exception as ex:  # pragma: no cover
        logger.debug(
            f"Calling {func} with args: {args} kw: {kwargs} failed\nException: {ex}"
        )
    return None


class AnnotationToValue(type):
    keys: t.List[str]

    @t.no_type_check
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        annotations = {}
        for base in reversed(bases):  # pragma: no cover
            annotations.update(getattr(base, "__annotations__", {}))
        annotations.update(namespace.get("__annotations__", {}))
        cls.keys = []
        for k, v in annotations.items():
            if type(v) is type(str):
                value = str(k).lower()
                setattr(cls, k, value)
                cls.keys.append(value)
        return cls

import inspect
from typing import Any


def get_function_name(func_class: Any) -> str:
    if inspect.isfunction(func_class) or inspect.isclass(func_class):
        return str(func_class.__name__)
    return str(func_class.__class__.__name__)

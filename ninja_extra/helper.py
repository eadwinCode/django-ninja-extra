import inspect
from typing import List, Callable, Any, Union, Type

from ninja.signature import is_async


def get_function_name(func_class: Any) -> str:
    if inspect.isfunction(func_class) or inspect.isclass(func_class):
        return func_class.__name__
    return func_class.__class__.__name__


class Helper:
    @classmethod
    def assign_route_auth_function_properties(cls, auth_functions: List[Union[Callable, Type]], view_func: Callable) -> List[Callable]:
        callbacks = []
        for callback in auth_functions:
            _call_back = callback if inspect.isfunction(callback) else callback.__call__
            if not getattr(callback, 'is_coroutine', None):
                callback.is_coroutine = is_async(_call_back)
            if is_async(_call_back) and not is_async(view_func):
                raise Exception(
                    f"Could apply auth=`{get_function_name(callback)}` "
                    f"to view_func=`{get_function_name(view_func)}`.\n"
                    f"N:B - {get_function_name(callback)} can only be used on Asynchronous view functions"
                )
            callbacks.append(callback)
        return callbacks

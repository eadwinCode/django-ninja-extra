import sys

from ninja.constants import NOT_SET

__all__ = ["asynccontextmanager", "NOT_SET_TYPE"]

if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager as asynccontextmanager  # noqa
else:  # pragma: no cover
    from contextlib2 import asynccontextmanager as asynccontextmanager  # noqa

try:
    from ninja.constants import NOT_SET_TYPE  # noqa
except Exception: # pragma: no cover
    NOT_SET_TYPE = type(NOT_SET)  # noqa

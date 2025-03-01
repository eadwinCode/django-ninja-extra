import contextvars
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from ninja_extra.context import RouteContext


POST = "POST"
PUT = "PUT"
PATCH = "PATCH"
DELETE = "DELETE"
GET = "GET"
HEAD = "HEAD"
OPTIONS = "OPTIONS"
TRACE = "TRACE"
ROUTE_METHODS = [POST, PUT, PATCH, DELETE, GET, HEAD, OPTIONS, TRACE]
THROTTLED_FUNCTION = "__throttled_endpoint__"
THROTTLED_OBJECTS = "__throttled_objects__"
ROUTE_FUNCTION = "__route_function__"

ROUTE_CONTEXT_VAR: contextvars.ContextVar[t.Optional["RouteContext"]] = (
    contextvars.ContextVar("ROUTE_CONTEXT_VAR")
)
ROUTE_CONTEXT_VAR.set(None)

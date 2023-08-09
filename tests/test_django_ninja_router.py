import pytest
from ninja.testing import TestClient

from ninja_extra import NinjaExtraAPI, Router
from ninja_extra.operation import PathView

from .schemas import UserSchema

api = NinjaExtraAPI(urls_namespace="ninja_router")


@api.get("/endpoint")
# view->api
def global_op(request) -> str:
    return "global"


@api.get("/return_type_response")
# view->api
def return_type_response(request) -> UserSchema:
    return {"name": "Eadwin", "age": 20}


@api.get("/return_type_response-2")
# view->api
def return_type_response_case_2(request) -> UserSchema:
    return UserSchema(name="Eadwin", age=20)


first_router = Router()


@first_router.get("/endpoint_1")
# view->router, router->api
def router_op1(request):
    return "first 1"


@first_router.post("/endpoint_1")
def router_op1_post(request):
    return "first 1"


second_router_one = Router()


@second_router_one.get("endpoint_1")
# view->router2, router2->router1, router1->api
def router_op2(request):
    return "second 1"


second_router_two = Router()


@second_router_two.get("endpoint_2")
# view->router2, router2->router1, router1->api
def router2_op3(request):
    return "second 2"


first_router.add_router("/second", second_router_one, tags=["one"])
first_router.add_router("/second", second_router_two, tags=["two"])
api.add_router("/first", first_router, tags=["global"])


@first_router.get("endpoint_2")
# router->api, view->router
def router1_op1(request):
    return "first 2"


@second_router_one.get("endpoint_3")
# router2->router1, router1->api, view->router2
def router21_op3(request, path_param: int = None):
    return "second 3" if path_param is None else f"second 3: {path_param}"


second_router_three = Router()


@second_router_three.get("endpoint_4")
# router1->api, view->router2, router2->router1
def router_op3(request, path_param: int = None):
    return "second 4" if path_param is None else f"second 4: {path_param}"


first_router.add_router("/second", second_router_three, tags=["three"])


client = TestClient(api)


@pytest.mark.parametrize(
    "path,expected_status,expected_response, action",
    [
        ("/endpoint", 200, "global", "get"),
        ("/first/endpoint_1", 200, "first 1", "get"),
        ("/first/endpoint_1", 200, "first 1", "post"),
        ("/first/endpoint_2", 200, "first 2", "get"),
        ("/first/second/endpoint_1", 200, "second 1", "get"),
        ("/first/second/endpoint_2", 200, "second 2", "get"),
        ("/first/second/endpoint_3", 200, "second 3", "get"),
        ("/first/second/endpoint_4", 200, "second 4", "get"),
    ],
)
def test_inheritance_responses(path, expected_status, expected_response, action):
    action_handler = getattr(client, action)
    response = action_handler(path)
    assert response.status_code == expected_status, response.content
    assert response.json() == expected_response


def test_router_path_view():
    router_op1_path_view = first_router.path_operations.get("/endpoint_1")
    assert router_op1_path_view
    assert isinstance(router_op1_path_view, PathView)

    global_op_path_view = api.default_router.path_operations.get("/endpoint")
    assert router_op1_path_view
    assert isinstance(global_op_path_view, PathView)


def test_return_response_type():
    res = client.get("/return_type_response")
    assert res.status_code == 200
    data = res.json()
    assert data == {"name": "Eadwin", "age": 20}

    res = client.get("/return_type_response-2")
    assert res.status_code == 200
    data = res.json()
    assert data == {"name": "Eadwin", "age": 20}

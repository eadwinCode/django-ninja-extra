from django.test import RequestFactory
from django.utils.translation import gettext_lazy as _

from ninja_extra import NinjaExtraAPI, exceptions, testing

api = NinjaExtraAPI(urls_namespace="exception")


@api.get("/list_exception")
def list_exception(request):
    raise exceptions.APIException(
        [
            "some error 1",
            "some error 2",
        ]
    )


@api.get("/list_exception_full_detail")
def list_exception_case_2(request):
    exception = exceptions.APIException(
        [
            "some error 1",
            "some error 2",
        ]
    )
    return exception.get_full_details()


@api.get("/dict_exception")
def dict_exception(request):
    raise exceptions.APIException({"error": "error 1"})


@api.get("/dict_exception_full_detail")
def dict_exception_full_detail(request):
    exception = exceptions.APIException({"error": "error 1"})
    return exception.get_full_details()


@api.get("/dict_exception_code_detail")
def dict_exception_code_detail(request):
    exception = exceptions.APIException({"error": "error 1"})
    return exception.get_codes()


@api.get("/list_exception_code_detail")
def list_exception_code_detail(request):
    exception = exceptions.APIException(["some error"])
    return exception.get_codes()


client = testing.TestClient(api)


class TestException:
    def test_get_error_details(self):
        example = "string"
        lazy_example = _(example)

        assert exceptions._get_error_details(lazy_example) == example

        assert isinstance(
            exceptions._get_error_details(lazy_example), exceptions.ErrorDetail
        )

        assert (
            exceptions._get_error_details({"nested": lazy_example})["nested"] == example
        )

        assert isinstance(
            exceptions._get_error_details({"nested": lazy_example})["nested"],
            exceptions.ErrorDetail,
        )

        assert exceptions._get_error_details([[lazy_example]])[0][0] == example

        assert isinstance(
            exceptions._get_error_details([[lazy_example]])[0][0],
            exceptions.ErrorDetail,
        )


class TestErrorDetail:
    def test_eq(self):
        assert exceptions.ErrorDetail("msg") == exceptions.ErrorDetail("msg")
        assert exceptions.ErrorDetail("msg", "code") == exceptions.ErrorDetail(
            "msg", code="code"
        )

        assert exceptions.ErrorDetail("msg") == "msg"
        assert exceptions.ErrorDetail("msg", "code") == "msg"

    def test_ne(self):
        assert exceptions.ErrorDetail("msg1") != exceptions.ErrorDetail("msg2")
        assert exceptions.ErrorDetail("msg") != exceptions.ErrorDetail(
            "msg", code="invalid"
        )

        assert exceptions.ErrorDetail("msg1") != "msg2"
        assert exceptions.ErrorDetail("msg1", "code") != "msg2"

    def test_repr(self):
        assert repr(
            exceptions.ErrorDetail("msg1")
        ) == "ErrorDetail(string={!r}, code=None)".format("msg1")
        assert repr(
            exceptions.ErrorDetail("msg1", "code")
        ) == "ErrorDetail(string={!r}, code={!r})".format("msg1", "code")

    def test_str(self):
        assert str(exceptions.ErrorDetail("msg1")) == "msg1"
        assert str(exceptions.ErrorDetail("msg1", "code")) == "msg1"

    def test_hash(self):
        assert hash(exceptions.ErrorDetail("msg")) == hash("msg")
        assert hash(exceptions.ErrorDetail("msg", "code")) == hash("msg")


def test_server_error():
    request = RequestFactory().get("/")
    response = exceptions.server_error(request)
    assert response.status_code == 500
    assert response["content-type"] == "application/json"


def test_bad_request():
    request = RequestFactory().get("/")
    exception = Exception("Something went wrong — Not used")
    response = exceptions.bad_request(request, exception)
    assert response.status_code == 400
    assert response["content-type"] == "application/json"


def test_exception_with_list_details():
    res = client.get("list_exception")
    assert res.status_code == 500
    assert res.json() == ["some error 1", "some error 2"]


def test_exception_with_list_full_details():
    res = client.get("list_exception_full_detail")
    assert res.status_code == 200
    assert res.json() == [
        {"message": "some error 1", "code": "error"},
        {"message": "some error 2", "code": "error"},
    ]


def test_exception_with_dict_details():
    res = client.get("dict_exception")
    assert res.status_code == 500
    assert res.json() == {"error": "error 1"}


def test_exception_with_full_details():
    res = client.get("dict_exception_full_detail")
    assert res.status_code == 200
    assert res.json() == {"error": {"message": "error 1", "code": "error"}}


def test_exception_dict_exception_code_detail():
    res = client.get("dict_exception_code_detail")
    assert res.status_code == 200
    assert res.json() == {"error": "error"}


def test_exception_with_list_exception_code_detail():
    res = client.get("list_exception_code_detail")
    assert res.status_code == 200
    assert res.json() == ["error"]


def test_validation_error():
    exception = exceptions.ValidationError()
    assert exception.detail == [
        exceptions.ErrorDetail(
            string=exceptions.ValidationError.default_detail,
            code=exceptions.ValidationError.default_code,
        )
    ]
    assert exception.get_codes() == [exceptions.ValidationError.default_code]

    exception = exceptions.ValidationError(["errors"])
    assert exception.detail == ["errors"]


def test_method_not_allowed_error():
    exception = exceptions.MethodNotAllowed("get")
    assert exception.detail == exceptions.MethodNotAllowed.default_detail.format(
        method="get"
    )
    assert exception.get_codes() == exceptions.MethodNotAllowed.default_code

    exception = exceptions.MethodNotAllowed("get", ["errors"])
    assert exception.detail == ["errors"]


def test_method_not_allowed_accepted_error():
    exception = exceptions.NotAcceptable()
    assert exception.detail == exceptions.NotAcceptable.default_detail
    assert exception.get_codes() == exceptions.NotAcceptable.default_code

    exception = exceptions.NotAcceptable(["errors"])
    assert exception.detail == ["errors"]


def test_unsupported_media_type_allowed_error():
    exception = exceptions.UnsupportedMediaType("whatever/type")
    assert exception.detail == exceptions.UnsupportedMediaType.default_detail.format(
        media_type="whatever/type"
    )
    assert exception.get_codes() == exceptions.UnsupportedMediaType.default_code

    exception = exceptions.UnsupportedMediaType("whatever/type", ["errors"])
    assert exception.detail == ["errors"]

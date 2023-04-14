from unittest import mock
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, User

from ninja_extra import ControllerBase, api_controller, http_get, permissions
from ninja_extra.testing import TestClient

anonymous_request = Mock()
anonymous_request.user = AnonymousUser()


class TestPermissionsCompositions:
    @classmethod
    def get_real_user_request(cls):
        _request = Mock()
        user = User.objects.create_user(
            username="eadwin", email="eadwin@example.com", password="password"
        )
        _request.user = user
        return _request

    @pytest.mark.parametrize(
        "method, auth, result",
        [
            ("GET", "", True),
            ("HEAD", "", True),
            ("OPTIONS", "", True),
            ("POST", "", False),
            ("PUT", "", False),
            ("PATCH", "", False),
            ("DELETE", "", False),
            ("POST", "Auth", True),
        ],
    )
    @pytest.mark.django_db
    def test_is_authenticated_and_read_only(self, method, auth, result):
        request = Mock()
        request.user = AnonymousUser()
        if auth:
            request = self.get_real_user_request()
        request.method = method
        assert (
            permissions.IsAuthenticatedOrReadOnly().has_permission(request, Mock())
            == result
        )

    def test_and_false(self):
        composed_perm = permissions.IsAuthenticated & permissions.AllowAny
        assert composed_perm().has_permission(anonymous_request, None) is False

    @pytest.mark.django_db
    def test_and_true(self):
        request = self.get_real_user_request()
        composed_perm = permissions.IsAuthenticated & permissions.AllowAny
        assert composed_perm().has_permission(request, None) is True

    def test_or_false(self):
        composed_perm = permissions.IsAuthenticated | permissions.AllowAny
        assert composed_perm().has_permission(anonymous_request, None) is True

    @pytest.mark.django_db
    def test_or_true(self):
        request = self.get_real_user_request()
        composed_perm = permissions.IsAuthenticated | permissions.AllowAny
        assert composed_perm().has_permission(request, None) is True

    def test_not_false(self):
        composed_perm = ~permissions.IsAuthenticated
        assert composed_perm().has_permission(anonymous_request, None) is True
        assert (
            composed_perm().has_object_permission(anonymous_request, None, None)
            is False
        )

    @pytest.mark.django_db
    def test_not_true(self):
        request = self.get_real_user_request()
        composed_perm = ~permissions.AllowAny
        assert composed_perm().has_permission(request, None) is False

    @pytest.mark.django_db
    def test_several_levels_without_negation(self):
        request = self.get_real_user_request()
        composed_perm = (
            permissions.IsAuthenticated
            & permissions.IsAuthenticated
            & permissions.IsAuthenticated
            & permissions.IsAuthenticated
        )
        assert composed_perm().has_permission(request, None) is True
        assert composed_perm().has_object_permission(request, None, None) is True

    @pytest.mark.django_db
    def test_several_levels_and_precedence_with_negation(self):
        request = self.get_real_user_request()
        composed_perm = (
            permissions.IsAuthenticated
            & ~permissions.IsAdminUser
            & permissions.IsAuthenticated
            & ~(permissions.IsAdminUser & permissions.IsAdminUser)
        )
        assert composed_perm().has_permission(request, None) is True

    @pytest.mark.django_db
    def test_several_levels_and_precedence(self):
        request = self.get_real_user_request()
        composed_perm = (
            permissions.IsAuthenticated & permissions.IsAuthenticated
            | permissions.IsAuthenticated & permissions.IsAuthenticated
        )
        assert composed_perm().has_permission(request, None) is True

    def test_or_lazyness(self):
        with mock.patch.object(
            permissions.AllowAny, "has_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.AllowAny | permissions.IsAuthenticated
                hasperm = composed_perm().has_permission(anonymous_request, None)
                assert hasperm is True
                assert mock_allow.call_count == 1
                mock_deny.assert_not_called()

        with mock.patch.object(
            permissions.AllowAny, "has_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.IsAuthenticated | permissions.AllowAny
                hasperm = composed_perm().has_permission(anonymous_request, None)
                assert hasperm is True
                assert mock_deny.call_count == 1
                assert mock_allow.call_count == 1

    def test_object_or_lazyness(self):
        with mock.patch.object(
            permissions.AllowAny, "has_object_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_object_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.AllowAny | permissions.IsAuthenticated
                hasperm = composed_perm().has_object_permission(
                    anonymous_request, None, None
                )
                assert hasperm is True
                assert mock_allow.call_count == 1
                mock_deny.assert_not_called()

        with mock.patch.object(
            permissions.AllowAny, "has_object_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_object_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.IsAuthenticated | permissions.AllowAny
                hasperm = composed_perm().has_object_permission(
                    anonymous_request, None, None
                )
                assert hasperm is True
                assert mock_deny.call_count == 1
                assert mock_allow.call_count == 1

    def test_and_lazyness(self):
        with mock.patch.object(
            permissions.AllowAny, "has_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.AllowAny & permissions.IsAuthenticated
                hasperm = composed_perm().has_permission(anonymous_request, None)
                assert hasperm is False
                assert mock_allow.call_count == 1
                assert mock_deny.call_count == 1

        with mock.patch.object(
            permissions.AllowAny, "has_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.IsAuthenticated & permissions.AllowAny
                hasperm = composed_perm().has_permission(anonymous_request, None)
                assert hasperm is False
                assert mock_deny.call_count == 1
                mock_allow.assert_not_called()

    def test_object_and_lazyness(self):
        with mock.patch.object(
            permissions.AllowAny, "has_object_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_object_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.AllowAny & permissions.IsAuthenticated
                hasperm = composed_perm().has_object_permission(
                    anonymous_request, None, None
                )
                assert hasperm is False
                assert mock_allow.call_count == 1
                assert mock_deny.call_count == 1

        with mock.patch.object(
            permissions.AllowAny, "has_object_permission", return_value=True
        ) as mock_allow:
            with mock.patch.object(
                permissions.IsAuthenticated, "has_object_permission", return_value=False
            ) as mock_deny:
                composed_perm = permissions.IsAuthenticated & permissions.AllowAny
                hasperm = composed_perm().has_object_permission(
                    anonymous_request, None, None
                )
                assert hasperm is False
                assert mock_deny.call_count == 1
                mock_allow.assert_not_called()


@api_controller(
    "permission/", permissions=[permissions.AllowAny, permissions.IsAdminUser()]
)
class Some2Controller(ControllerBase):
    @http_get("index/")
    def index(self):
        return {"success": True}

    @http_get(
        "permission/",
        permissions=[permissions.IsAdminUser() & permissions.IsAuthenticatedOrReadOnly],
    )
    def permission_accept_type_and_instance(self):
        return {"success": True}


@pytest.mark.django_db
@pytest.mark.parametrize("route", ["permission/", "index/"])
def test_permission_controller_instance(route):
    user = User.objects.create_user(
        username="eadwin",
        email="eadwin@example.com",
        password="password",
        is_staff=True,
        is_superuser=True,
    )

    client = TestClient(Some2Controller)
    res = client.get(route, user=AnonymousUser())
    assert res.status_code == 403

    res = client.get(route, user=user)
    assert res.status_code == 200
    assert res.json() == {"success": True}

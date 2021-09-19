from unittest import mock
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, User

from ninja_extra import permissions

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

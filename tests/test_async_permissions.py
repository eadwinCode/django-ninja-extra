from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from injector import inject

from ninja_extra import (
    ControllerBase,
    api_controller,
    get_injector,
    http_get,
    http_post,
    permissions,
)
from ninja_extra.permissions.base import AsyncBasePermission
from ninja_extra.testing import TestAsyncClient


# Create mock requests for testing
@pytest.fixture
def anonymous_request():
    _request = Mock()
    _request.user = AnonymousUser()
    return _request


@pytest.fixture
def authenticated_request():
    _request = Mock()
    _request.user = Mock(is_authenticated=True, is_staff=False)
    return _request


@pytest.fixture
def admin_request():
    _request = Mock()
    _request.user = Mock(is_authenticated=True, is_staff=True)
    return _request


# Custom async permissions for testing
class TestAsyncPermission(AsyncBasePermission):
    """Custom async permission that returns a specified result"""

    def __init__(self, result=True):
        self.result = result
        self.message = "Test permission"

    def has_permission(self, request, controller):
        return self.result

    async def has_permission_async(self, request, controller):
        return self.result


class PermissionCalledTracker(AsyncBasePermission):
    """Permission that tracks when it's called"""

    def __init__(self, result=True):
        self.result = result
        self.called_sync = False
        self.called_async = False
        self.message = "Tracker permission"

    def has_permission(self, request, controller):
        self.called_sync = True
        return self.result

    async def has_permission_async(self, request, controller):
        self.called_async = True
        return self.result


class TestAsyncPermissionOperators:
    """Tests for the AND, OR, NOT operators with async permissions"""

    @pytest.mark.asyncio
    async def test_and_operator_both_true(self):
        """Test AND operator with both permissions returning True"""
        perm1 = TestAsyncPermission(True)
        perm2 = TestAsyncPermission(True)
        combined = perm1 & perm2

        assert await combined.has_permission_async(None, None) is True

    @pytest.mark.asyncio
    async def test_and_operator_first_false(self):
        """Test AND operator with first permission returning False"""
        perm1 = TestAsyncPermission(False)
        perm2 = TestAsyncPermission(True)
        combined = perm1 & perm2

        tracker1 = PermissionCalledTracker(False)
        tracker2 = PermissionCalledTracker(True)
        combined_trackers = tracker1 & tracker2

        assert await combined.has_permission_async(None, None) is False
        assert await combined_trackers.has_permission_async(None, None) is False

        # Second permission should not be called (short-circuit)
        assert tracker1.called_async is True
        assert tracker2.called_async is False

    @pytest.mark.asyncio
    async def test_and_operator_second_false(self):
        """Test AND operator with second permission returning False"""
        perm1 = TestAsyncPermission(True)
        perm2 = TestAsyncPermission(False)
        combined = perm1 & perm2

        assert await combined.has_permission_async(None, None) is False

    @pytest.mark.asyncio
    async def test_or_operator_both_true(self):
        """Test OR operator with both permissions returning True"""
        perm1 = TestAsyncPermission(True)
        perm2 = TestAsyncPermission(True)
        combined = perm1 | perm2

        tracker1 = PermissionCalledTracker(True)
        tracker2 = PermissionCalledTracker(True)
        combined_trackers = tracker1 | tracker2

        assert await combined.has_permission_async(None, None) is True
        assert await combined_trackers.has_permission_async(None, None) is True

        # Second permission should not be called (short-circuit)
        assert tracker1.called_async is True
        assert tracker2.called_async is False

    @pytest.mark.asyncio
    async def test_or_operator_first_false(self):
        """Test OR operator with first permission returning False"""
        perm1 = TestAsyncPermission(False)
        perm2 = TestAsyncPermission(True)
        combined = perm1 | perm2

        assert await combined.has_permission_async(None, None) is True

    @pytest.mark.asyncio
    async def test_or_operator_both_false(self):
        """Test OR operator with both permissions returning False"""
        perm1 = TestAsyncPermission(False)
        perm2 = TestAsyncPermission(False)
        combined = perm1 | perm2

        assert await combined.has_permission_async(None, None) is False

    @pytest.mark.asyncio
    async def test_not_operator_true(self):
        """Test NOT operator with permission returning True"""
        perm = TestAsyncPermission(True)
        negated = ~perm

        assert await negated.has_permission_async(None, None) is False

    @pytest.mark.asyncio
    async def test_not_operator_false(self):
        """Test NOT operator with permission returning False"""
        perm = TestAsyncPermission(False)
        negated = ~perm

        assert await negated.has_permission_async(None, None) is True

    @pytest.mark.asyncio
    async def test_complex_expression(self):
        """Test complex expression with multiple operators"""
        perm1 = TestAsyncPermission(True)
        perm2 = TestAsyncPermission(False)
        perm3 = TestAsyncPermission(True)

        # (True AND False) OR (NOT True) = False OR False = False
        and_op = perm1 & perm2
        not_op = ~perm3
        expression = and_op | not_op
        assert await expression.has_permission_async(None, None) is False

        # (True OR False) AND (NOT False) = True AND True = True
        or_op = perm1 | perm2
        not_op = ~TestAsyncPermission(False)
        expression = or_op & not_op
        assert await expression.has_permission_async(None, None) is True


class TestMixedSyncAsyncPermissions:
    """Tests for mixing sync and async permissions"""

    @pytest.mark.asyncio
    async def test_sync_and_async_and(self, authenticated_request, admin_request):
        """Test AND operator with sync and async permissions"""
        sync_perm = permissions.IsAuthenticated()
        async_perm = permissions.IsAdminUser()

        # IsAuthenticated & IsAdminUser
        combined = sync_perm & async_perm

        # Anonymous user - should fail first check
        anon_user = Mock(is_authenticated=False)
        anon_request = Mock(user=anon_user)
        assert await combined.has_permission_async(anon_request, None) is False

        # Authenticated non-admin - should pass first check, fail second
        assert await combined.has_permission_async(authenticated_request, None) is False

        # Admin user - should pass both checks
        assert await combined.has_permission_async(admin_request, None) is True

    @pytest.mark.asyncio
    async def test_sync_and_async_or(self, authenticated_request):
        """Test OR operator with sync and async permissions"""
        sync_perm = permissions.IsAuthenticated()
        async_perm = permissions.AllowAny()

        # IsAuthenticated | AllowAny
        combined = sync_perm | async_perm

        # Anonymous user - should fail first check, pass second
        anon_user = Mock(is_authenticated=False)
        anon_request = Mock(user=anon_user)
        assert await combined.has_permission_async(anon_request, None) is True

        # Authenticated user - should pass first check, short-circuit
        tracker1 = PermissionCalledTracker(True)  # Sync perm
        tracker2 = PermissionCalledTracker(True)  # Async perm
        combined_trackers = tracker1 | tracker2

        assert (
            await combined_trackers.has_permission_async(authenticated_request, None)
            is True
        )
        assert tracker1.called_async is True
        assert tracker2.called_async is False

    @pytest.mark.asyncio
    async def test_inverted_mixed_permission(self, authenticated_request):
        """Test inverting a mixed permission"""
        # NOT IsAuthenticated
        inverted = ~permissions.IsAuthenticated()

        # Should be False for authenticated user
        assert await inverted.has_permission_async(authenticated_request, None) is False

        # Should be True for anonymous user
        anon_user = Mock(is_authenticated=False)
        anon_request = Mock(user=anon_user)
        assert await inverted.has_permission_async(anon_request, None) is True


@api_controller(
    "permission/", permissions=[permissions.AllowAny, permissions.IsAdminUser()]
)
class AsyncController(ControllerBase):
    @http_get("index/")
    async def index(self):
        return {"success": True}

    @http_get(
        "permission/",
        permissions=[
            permissions.IsAdminUser() & permissions.IsAuthenticatedOrReadOnly()
        ],
    )
    async def permission_accept_type_and_instance(self):
        return {"success": True}

    @http_get(
        "permission/async/",
        permissions=[permissions.IsAdminUser() & permissions.IsAuthenticatedOrReadOnly],
    )
    async def permission_accept_type_and_instance_async(self):
        return {"success": True}


class TestAsyncController:
    """Tests for the AsyncController class with async permissions"""

    @pytest.mark.asyncio
    async def test_controller_level_permissions(self):
        """Test controller-level permissions (AllowAny & IsAdminUser)"""
        # Create admin and normal users
        admin_user = Mock(is_authenticated=True, is_staff=True)
        normal_user = Mock(is_authenticated=True, is_staff=False)
        anon_user = AnonymousUser()

        # Use TestAsyncClient directly with the controller class
        client = TestAsyncClient(AsyncController)

        # Anonymous user should be rejected by IsAdminUser
        response = await client.get("/index/", user=anon_user)
        assert response.status_code == 403

        # Normal authenticated user should be rejected by IsAdminUser
        response = await client.get("/index/", user=normal_user)
        assert response.status_code == 403

        # Admin user should be allowed
        response = await client.get("/index/", user=admin_user)
        assert response.status_code == 200
        assert response.json() == {"success": True}

    @pytest.mark.asyncio
    async def test_route_level_permissions(self):
        """Test route-level permissions (IsAdminUser & IsAuthenticatedOrReadOnly)"""
        # Create admin and normal users
        admin_user = Mock(is_authenticated=True, is_staff=True)
        normal_user = Mock(is_authenticated=True, is_staff=False)
        anon_user = AnonymousUser()

        # Use TestAsyncClient directly with the controller class
        client = TestAsyncClient(AsyncController)

        # Anonymous user making a GET request should be rejected because of combined permissions
        response = await client.get("/permission/", user=anon_user)
        assert response.status_code == 403

        # Normal authenticated user should be rejected by IsAdminUser
        response = await client.get("/permission/", user=normal_user)
        assert response.status_code == 403

        # Admin user should be allowed
        response = await client.get("/permission/", user=admin_user)
        assert response.status_code == 200
        assert response.json() == {"success": True}

    @pytest.mark.asyncio
    async def test_route_level_permissions_with_class_reference(self):
        """Test route-level permissions with class reference (IsAdminUser & IsAuthenticatedOrReadOnly)"""
        # Create admin and normal users
        admin_user = Mock(is_authenticated=True, is_staff=True)
        normal_user = Mock(is_authenticated=True, is_staff=False)
        anon_user = AnonymousUser()

        # Use TestAsyncClient directly with the controller class
        client = TestAsyncClient(AsyncController)

        # Anonymous user making a GET request should be rejected because of combined permissions
        response = await client.get("/permission/async/", user=anon_user)
        assert response.status_code == 403

        # Normal authenticated user should be rejected by IsAdminUser
        response = await client.get("/permission/async/", user=normal_user)
        assert response.status_code == 403

        # Admin user should be allowed
        response = await client.get("/permission/async/", user=admin_user)
        assert response.status_code == 200
        assert response.json() == {"success": True}

    @pytest.mark.asyncio
    async def test_permissions_with_different_http_methods(self):
        """Test IsAuthenticatedOrReadOnly permission with different HTTP methods"""

        # Create a new controller to test IsAuthenticatedOrReadOnly
        @api_controller("read-only")
        class ReadOnlyController(ControllerBase):
            @http_get(
                "resource/", permissions=[permissions.IsAuthenticatedOrReadOnly()]
            )
            async def get_resource(self):
                return {"success": True}

            @http_post(
                "resource/", permissions=[permissions.IsAuthenticatedOrReadOnly()]
            )
            async def post_resource(self):
                return {"success": True}

        # Initialize the async test client with the controller class
        client = TestAsyncClient(ReadOnlyController)

        # Create authenticated and anonymous users
        auth_user = Mock(is_authenticated=True)
        anon_user = AnonymousUser()

        # Anonymous user with GET (read) should be allowed
        response = await client.get("/resource/", user=anon_user)
        assert response.status_code == 200

        # Anonymous user with POST (write) should be rejected
        response = await client.post("/resource/", user=anon_user)
        assert response.status_code == 403

        # Authenticated user should be allowed for GET
        response = await client.get("/resource/", user=auth_user)
        assert response.status_code == 200

        # Authenticated user should be allowed for POST
        response = await client.post("/resource/", user=auth_user)
        assert response.status_code == 200


class TestInjectablePermissions:
    """Tests for permission classes that use dependency injection with @inject"""

    @pytest.mark.asyncio
    async def test_injectable_permission_resolve(self):
        """Test that permission classes with @inject are resolved correctly"""

        # Create a service to be injected
        class AuthService:
            def is_admin(self, user):
                return user.is_staff

            def is_authenticated(self, user):
                return user.is_authenticated

        # Create a permission class that uses dependency injection
        class InjectablePermission(AsyncBasePermission):
            @inject
            def __init__(self, auth_service: AuthService):
                self.auth_service = auth_service
                self.message = "Must be admin"

            async def has_permission_async(self, request, controller):
                return self.auth_service.is_admin(request.user)

        # Register service with the injector
        injector = get_injector()
        injector.binder.bind(AuthService)
        injector.binder.bind(InjectablePermission)

        # Test resolving the permission directly
        resolved_perm = InjectablePermission.resolve()

        # Create request mocks for testing
        admin_request = Mock(user=Mock(is_staff=True, is_authenticated=True))
        normal_request = Mock(user=Mock(is_staff=False, is_authenticated=True))

        # Test permission check works
        assert resolved_perm.has_permission(admin_request, None) is True
        assert resolved_perm.has_permission(normal_request, None) is False

        # Test async permission check works
        assert await resolved_perm.has_permission_async(admin_request, None) is True
        assert await resolved_perm.has_permission_async(normal_request, None) is False

    @pytest.mark.asyncio
    async def test_injectable_permissions_with_operators(self):
        """Test injected permissions with operators (AND, OR, NOT)"""

        # Create services to be injected
        class AuthService:
            def is_admin(self, user):
                return user.is_staff

            def is_authenticated(self, user):
                return user.is_authenticated

        class PermissionService:
            def is_special_user(self, user):
                return getattr(user, "is_special", False)

        # Create permission classes that use dependency injection

        class AdminPermission(AsyncBasePermission):
            @inject
            def __init__(self, auth_service: AuthService):
                self.auth_service = auth_service
                self.message = "Must be admin"

            async def has_permission_async(self, request, controller):
                return self.auth_service.is_admin(request.user)

        class SpecialUserPermission(AsyncBasePermission):
            @inject
            def __init__(self, permission_service: PermissionService):
                self.permission_service = permission_service
                self.message = "Must be special user"

            async def has_permission_async(self, request, controller):
                return self.permission_service.is_special_user(request.user)

        # Register services with the injector
        injector = get_injector()
        injector.binder.bind(AuthService, to=AuthService)
        injector.binder.bind(PermissionService, to=PermissionService)

        # Create combined permissions using logical operators
        and_perm = AdminPermission & SpecialUserPermission
        or_perm = AdminPermission | SpecialUserPermission
        not_perm = ~AdminPermission

        # Create request mocks for testing
        admin_special_request = Mock(
            user=Mock(is_staff=True, is_authenticated=True, is_special=True)
        )
        admin_request = Mock(
            user=Mock(is_staff=True, is_authenticated=True, is_special=False)
        )
        special_request = Mock(
            user=Mock(is_staff=False, is_authenticated=True, is_special=True)
        )
        normal_request = Mock(
            user=Mock(is_staff=False, is_authenticated=True, is_special=False)
        )

        # AND permission - requires both admin and special
        and_result = await and_perm.has_permission_async(admin_special_request, None)
        assert and_result is True
        and_result = await and_perm.has_permission_async(admin_request, None)
        assert and_result is False
        and_result = await and_perm.has_permission_async(special_request, None)
        assert and_result is False

        # OR permission - requires either admin or special
        or_result = await or_perm.has_permission_async(admin_special_request, None)
        assert or_result is True
        or_result = await or_perm.has_permission_async(admin_request, None)
        assert or_result is True
        or_result = await or_perm.has_permission_async(special_request, None)
        assert or_result is True
        or_result = await or_perm.has_permission_async(normal_request, None)
        assert or_result is False

        # NOT permission - requires NOT admin
        not_result = await not_perm.has_permission_async(admin_request, None)
        assert not_result is False
        not_result = await not_perm.has_permission_async(normal_request, None)
        assert not_result is True

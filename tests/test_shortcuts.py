import pytest
from django.contrib.auth.models import Group, Permission
from django.db.models import QuerySet

from ninja_extra import status
from ninja_extra.exceptions import APIException, NotFound
from ninja_extra.shortcuts import (
    _get_queryset,
    _validate_queryset,
    get_object_or_exception,
    get_object_or_none,
)


class CustomException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class TestModelUtils:
    @pytest.mark.django_db
    def test_get_object_or_exception_should_return_object(self):
        group = Group.objects.create(name="_groupowner")
        saved_perm = get_object_or_exception(Group, id=group.id)
        assert saved_perm

    @pytest.mark.django_db
    def test_get_object_or_exception_should_raise_exception(self):
        with pytest.raises(NotFound) as exception_info:
            get_object_or_exception(Permission, id=0)
        assert "Permission with id = 0  was not found" == exception_info.value.detail
        assert exception_info.value.status_code == 404

    @pytest.mark.django_db
    def test_get_object_or_exception_with_error_message(self):
        with pytest.raises(NotFound) as exception_info:
            get_object_or_exception(Permission, error_message="Not found", id=0)
        assert "Not found" in str(exception_info.value.detail)

    @pytest.mark.django_db
    def test_get_object_or_exception_with_custom_exception(self):
        with pytest.raises(CustomException) as exception_info:
            get_object_or_exception(
                Permission, error_message="Bad Request", id=0, exception=CustomException
            )
        assert "Bad Request" in str(exception_info.value.detail)
        assert exception_info.value.status_code == 400

    @pytest.mark.django_db
    def test_get_object_or_none_with_error_message(self):
        obj = get_object_or_none(Permission, id=0)
        assert obj is None

    @pytest.mark.django_db
    def test__get_queryset(self):
        query_set = _get_queryset(Permission)
        assert isinstance(query_set, QuerySet)
        query_set_new = _get_queryset(query_set)
        assert query_set_new == query_set

    @pytest.mark.django_db
    def test__validate_queryset(self):
        class FakeQuerySet:
            pass

        query_set = _get_queryset(Permission)
        assert _validate_queryset(Permission, query_set) is None
        with pytest.raises(ValueError):
            _validate_queryset(Permission, FakeQuerySet)

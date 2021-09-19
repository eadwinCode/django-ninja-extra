import pytest
from django.contrib.auth.models import Group, Permission

from ninja_extra import status
from ninja_extra.exceptions import APIException, NotFound
from ninja_extra.shortcuts import get_object_or_exception, get_object_or_none


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
        assert "Permission with id = 0  was not found" == exception_info.value.message
        assert exception_info.value.status_code == 404

    @pytest.mark.django_db
    def test_get_object_or_exception_with_error_message(self):
        with pytest.raises(NotFound) as exception_info:
            get_object_or_exception(Permission, error_message="Not found", id=0)
        assert "Not found" in str(exception_info.value.message)

    @pytest.mark.django_db
    def test_get_object_or_exception_with_custom_exception(self):
        with pytest.raises(CustomException) as exception_info:
            get_object_or_exception(
                Permission, error_message="Bad Request", id=0, exception=CustomException
            )
        assert "Bad Request" in str(exception_info.value.message)
        assert exception_info.value.status_code == 400

    @pytest.mark.django_db
    def test_get_object_or_none_with_error_message(self):
        obj = get_object_or_none(Permission, id=0)
        assert obj is None

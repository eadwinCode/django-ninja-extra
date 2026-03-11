from datetime import date
from typing import Any, Optional, Type

import pytest
from django.db.models import QuerySet

from ninja_extra import ModelService, status
from ninja_extra.exceptions import APIException, NotFound
from ninja_extra.testing import TestClient

from ..models import Category, Event
from .model_service_with_sample import EventModelController


class CustomBadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST


class FilteredEventModelService(ModelService):
    def get_one(
        self,
        pk: Any,
        queryset: Optional[QuerySet] = None,
        error_message: Optional[str] = None,
        exception: Type[APIException] = NotFound,
        **kwargs: Any,
    ) -> Any:
        queryset = self.model.objects.all() if queryset is None else queryset
        return super().get_one(
            pk=pk,
            queryset=queryset.filter(category__isnull=False),
            error_message=error_message,
            exception=exception,
            **kwargs,
        )


class DeepInheritedEventModelService(FilteredEventModelService):
    def get_one(
        self,
        pk: Any,
        queryset: Optional[QuerySet] = None,
        error_message: Optional[str] = "Missing allowed event",
        exception: Type[APIException] = CustomBadRequest,
        **kwargs: Any,
    ) -> Any:
        queryset = self.model.objects.all() if queryset is None else queryset
        return super().get_one(
            pk=pk,
            queryset=queryset.filter(title__startswith="Allowed"),
            error_message=error_message,
            exception=exception,
            **kwargs,
        )


@pytest.mark.django_db
def test_model_service_injection():
    client = TestClient(EventModelController)
    # POST
    res = client.post(
        "/",
        json={
            "start_date": "2020-01-01",
            "end_date": "2020-01-02",
            "title": "Testing ModelService Injection",
        },
    )
    assert res.status_code == 201
    data = res.json()

    res = client.get(f"/{data['id']}")
    data = res.json()

    data.pop("id")
    assert data == {
        "end_date": "2020-01-02",
        "start_date": "2020-01-01",
        "title": "Testing ModelService Injection",
        "category": None,
    }
    assert res.status_code == 200


@pytest.mark.django_db
def test_model_service_get_one_supports_queryset_error_message_and_exception():
    category = Category.objects.create(title="Allowed category")
    event = Event.objects.create(
        title="Allowed event",
        category=category,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 2),
    )
    service = ModelService(model=Event)

    result = service.get_one(
        pk=event.pk,
        queryset=Event.objects.filter(title__startswith="Allowed"),
    )

    assert result == event

    with pytest.raises(CustomBadRequest) as exception_info:
        service.get_one(
            pk=event.pk,
            queryset=Event.objects.filter(title__startswith="Blocked"),
            error_message="Blocked from lookup",
            exception=CustomBadRequest,
        )

    assert exception_info.value.detail == "Blocked from lookup"
    assert exception_info.value.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_model_service_get_one_supports_queryset_super_chaining():
    allowed_category = Category.objects.create(title="Allowed category")
    blocked_category = Category.objects.create(title="Blocked category")
    allowed_event = Event.objects.create(
        title="Allowed event",
        category=allowed_category,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 2),
    )
    blocked_event = Event.objects.create(
        title="Blocked event",
        category=blocked_category,
        start_date=date(2020, 1, 3),
        end_date=date(2020, 1, 4),
    )
    service = DeepInheritedEventModelService(model=Event)

    result = service.get_one(pk=allowed_event.pk)

    assert result == allowed_event

    with pytest.raises(CustomBadRequest) as exception_info:
        service.get_one(pk=blocked_event.pk)

    assert exception_info.value.detail == "Missing allowed event"

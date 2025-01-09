import pytest

from ninja_extra.testing import TestClient

from .model_service_with_sample import EventModelController


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

"""
Tests for the lookup_field configuration in ModelController.

The lookup_field option allows using a different field for object lookups
instead of the default primary key ('pk'). This is similar to Django REST
Framework's lookup_field option.
"""

import pytest

from ninja_extra.testing import TestClient

from ..models import Client
from .samples import ClientModelControllerWithLookupField


@pytest.mark.django_db
def test_model_controller_with_lookup_field():
    """
    Test that ModelController correctly uses lookup_field='key' for all CRUD operations.

    The Client model has a unique 'key' field, and this test verifies that:
    - URLs use the key field (/{str:key}) instead of pk (/{int:id})
    - GET, PUT, PATCH, DELETE operations lookup by key
    """
    client = TestClient(ClientModelControllerWithLookupField)

    # CREATE - Create a new client with a unique key
    test_key = "test-client-key-123"
    res = client.post("/", json={"key": test_key})
    assert res.status_code == 201
    data = res.json()
    assert data["key"] == test_key
    client_id = data["id"]

    # GET by key (not by id) - This is the key feature of lookup_field
    res = client.get(f"/{test_key}")
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == test_key
    assert data["id"] == client_id

    # LIST - should still work normally
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert any(item["key"] == test_key for item in data)

    # PUT by key - Update the client using key as lookup
    new_key = "updated-key-456"
    res = client.put(f"/{test_key}", json={"key": new_key})
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == new_key
    assert data["id"] == client_id  # Same id, different key

    # PATCH by key - Patch the client using the new key
    patched_key = "patched-key-789"
    res = client.patch(f"/{new_key}", json={"key": patched_key})
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == patched_key
    assert data["id"] == client_id

    # DELETE by key
    res = client.delete(f"/{patched_key}")
    assert res.status_code == 204

    # Verify the client is deleted
    assert not Client.objects.filter(key=patched_key).exists()


@pytest.mark.django_db
def test_model_controller_lookup_field_not_found():
    """
    Test that using a non-existent key returns 404.
    """
    client = TestClient(ClientModelControllerWithLookupField)

    # GET with non-existent key should return 404
    res = client.get("/non-existent-key")
    assert res.status_code == 404

    # PUT with non-existent key should return 404
    res = client.put("/non-existent-key", json={"key": "new-key"})
    assert res.status_code == 404

    # PATCH with non-existent key should return 404
    res = client.patch("/non-existent-key", json={"key": "new-key"})
    assert res.status_code == 404

    # DELETE with non-existent key should return 404
    res = client.delete("/non-existent-key")
    assert res.status_code == 404


@pytest.mark.django_db
def test_lookup_field_uses_correct_url_parameter_type():
    """
    Test that the URL parameter type matches the lookup field type.

    For 'key' (CharField), the URL should use string type: /{str:key}
    """
    client = TestClient(ClientModelControllerWithLookupField)

    # Create a client with a key containing special characters that are valid in URLs
    special_key = "client-with-dashes"
    res = client.post("/", json={"key": special_key})
    assert res.status_code == 201

    # Access using the string key
    res = client.get(f"/{special_key}")
    assert res.status_code == 200
    assert res.json()["key"] == special_key

    # Cleanup
    Client.objects.filter(key=special_key).delete()

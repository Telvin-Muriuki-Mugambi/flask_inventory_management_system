import pytest

from API.app import create_app
from API.inventory import InventoryStore
from Fetch import OpenFoodFactsError


class FakeProductClient:
    def __init__(self):
        self.barcode_product = {
            "barcode": "3017624010701",
            "name": "Nutella",
            "brands": "Ferrero",
            "quantity": "400 g",
            "image_url": None,
            "categories": None,
        }
        self.search_results = [self.barcode_product]
        self.should_fail = False
        self.last_barcode = None
        self.last_name = None

    def get_by_barcode(self, barcode):
        self.last_barcode = barcode
        if self.should_fail:
            raise OpenFoodFactsError("service unavailable")
        if barcode == self.barcode_product["barcode"]:
            return self.barcode_product
        return None

    def search_by_name(self, name):
        self.last_name = name
        if self.should_fail:
            raise OpenFoodFactsError("service unavailable")
        return self.search_results


@pytest.fixture
def api_context():
    product_client = FakeProductClient()
    app = create_app(InventoryStore(), product_client)
    return app.test_client(), product_client


def test_list_inventory_starts_empty(api_context):
    client, _ = api_context
    response = client.get("/inventory")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_read_update_and_delete_item(api_context):
    client, _ = api_context
    create_response = client.post(
        "/inventory",
        json={"name": "Oat milk", "quantity": 12, "price": 3.5,
              "barcode": "1234567890123"},
    )
    item = create_response.get_json()

    assert create_response.status_code == 201
    assert create_response.headers["Location"] == "/inventory/1"
    assert item["id"] == 1
    assert item["barcode"] == "1234567890123"

    read_response = client.get("/inventory/1")
    assert read_response.status_code == 200
    assert read_response.get_json() == item

    update_response = client.patch("/inventory/1", json={"quantity": 8})
    assert update_response.status_code == 200
    assert update_response.get_json()["quantity"] == 8

    delete_response = client.delete("/inventory/1")
    assert delete_response.status_code == 204
    assert client.get("/inventory/1").status_code == 404


def test_create_rejects_missing_and_invalid_fields(api_context):
    client, _ = api_context
    missing_field_response = client.post(
        "/inventory", json={"name": "Oat milk"}
    )
    invalid_quantity_response = client.post(
        "/inventory", json={"name": "Oat milk", "quantity": -1, "price": 3.5}
    )

    assert missing_field_response.status_code == 400
    assert "error" in missing_field_response.get_json()
    assert invalid_quantity_response.status_code == 400


def test_update_rejects_empty_patch_and_unknown_item(api_context):
    client, _ = api_context
    empty_patch_response = client.patch("/inventory/1", json={})
    missing_item_response = client.patch("/inventory/1", json={"quantity": 3})

    assert empty_patch_response.status_code == 400
    assert missing_item_response.status_code == 404


def test_barcode_lookup_returns_external_product_without_storing_it(api_context):
    client, product_client = api_context
    response = client.get("/products/barcode/3017624010701")

    assert response.status_code == 200
    assert response.get_json()["product"]["name"] == "Nutella"
    assert product_client.last_barcode == "3017624010701"
    assert client.get("/inventory").get_json() == []


def test_barcode_lookup_handles_invalid_or_unknown_products(api_context):
    client, _ = api_context
    invalid_response = client.get("/products/barcode/abc")
    missing_response = client.get("/products/barcode/0000000000000")

    assert invalid_response.status_code == 400
    assert missing_response.status_code == 404


def test_name_search_returns_matches_and_requires_a_name(api_context):
    client, product_client = api_context
    response = client.get("/products/search?name=Nutella")
    missing_name_response = client.get("/products/search")

    assert response.status_code == 200
    assert response.get_json()["count"] == 1
    assert product_client.last_name == "Nutella"
    assert missing_name_response.status_code == 400


def test_lookup_reports_external_service_failure(api_context):
    client, product_client = api_context
    product_client.should_fail = True

    barcode_response = client.get("/products/barcode/3017624010701")
    search_response = client.get("/products/search?name=Nutella")

    assert barcode_response.status_code == 502
    assert search_response.status_code == 502
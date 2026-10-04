import io
import json
from contextlib import redirect_stderr, redirect_stdout
from urllib.error import HTTPError

import pytest

from CLI.api_client import ApiClientError, InventoryApiClient
from CLI.main import main


class FakeResponse:
    def __init__(self, payload=b"{}"):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.payload


class FakeCliApi:
    def __init__(self):
        self.calls = []

    def list_inventory(self):
        self.calls.append(("list",))
        return []

    def get_inventory_item(self, item_id):
        self.calls.append(("get", item_id))
        return {"id": item_id}

    def add_inventory_item(self, item):
        self.calls.append(("add", item))
        return {"id": 1, **item}

    def update_inventory_item(self, item_id, changes):
        self.calls.append(("update", item_id, changes))
        return {"id": item_id, **changes}

    def delete_inventory_item(self, item_id):
        self.calls.append(("delete", item_id))

    def lookup_barcode(self, barcode):
        self.calls.append(("barcode", barcode))
        return {"barcode": barcode}

    def search_products(self, name):
        self.calls.append(("search", name))
        return {"products": []}


def test_client_posts_json_to_configured_api(monkeypatch):
    requests = []

    def fake_urlopen(request, timeout=None):
        requests.append(request)
        return FakeResponse(b'{"id": 1}')

    monkeypatch.setattr("CLI.api_client.urlopen", fake_urlopen)
    client = InventoryApiClient("http://localhost:5001/")

    result = client.add_inventory_item({"name": "Tea", "quantity": 2, "price": 4})

    request = requests[0]
    assert result == {"id": 1}
    assert request.full_url == "http://localhost:5001/inventory"
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {
        "name": "Tea", "quantity": 2, "price": 4
    }


def test_client_encodes_name_query(monkeypatch):
    requests = []

    def fake_urlopen(request, timeout=None):
        requests.append(request)
        return FakeResponse(b'{"products": []}')

    monkeypatch.setattr("CLI.api_client.urlopen", fake_urlopen)
    client = InventoryApiClient()

    client.search_products("oat milk & honey")

    assert "name=oat+milk+%26+honey" in requests[0].full_url


def test_client_converts_api_errors(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise HTTPError(
            "http://localhost/inventory/88",
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"error": "Inventory item not found."}'),
        )

    monkeypatch.setattr("CLI.api_client.urlopen", fake_urlopen)

    with pytest.raises(ApiClientError, match="HTTP 404"):
        InventoryApiClient().get_inventory_item(88)


@pytest.fixture
def fake_cli_api():
    return FakeCliApi()


def run_cli(args, client):
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(args, client=client)
    return exit_code, output.getvalue()


def test_add_and_update_commands_build_payloads(fake_cli_api):
    add_code, add_output = run_cli(
        ["add", "Oat milk", "12", "3.5", "--barcode", "12345"], fake_cli_api
    )
    update_code, update_output = run_cli(
        ["update", "7", "--quantity", "8"], fake_cli_api
    )

    assert add_code == 0
    assert update_code == 0
    assert '"barcode": "12345"' in add_output
    assert '"quantity": 8' in update_output
    assert fake_cli_api.calls == [
        ("add", {
            "name": "Oat milk",
            "quantity": 12,
            "price": 3.5,
            "barcode": "12345",
        }),
        ("update", 7, {"quantity": 8}),
    ]


def test_search_and_delete_commands(fake_cli_api):
    search_code, search_output = run_cli(["search", "Oat milk"], fake_cli_api)
    delete_code, delete_output = run_cli(["delete", "4"], fake_cli_api)

    assert search_code == 0
    assert delete_code == 0
    assert '"products": []' in search_output
    assert "Deleted inventory item 4" in delete_output
    assert fake_cli_api.calls == [("search", "Oat milk"), ("delete", 4)]


def test_help_command_prints_usage_without_calling_api(fake_cli_api):
    exit_code, output = run_cli(["help"], fake_cli_api)

    assert exit_code == 0
    assert "usage:" in output
    assert "{list,get,add,update,delete,barcode,search,help}" in output
    assert fake_cli_api.calls == []


def test_api_errors_are_printed_to_stderr():
    class FailingApi(FakeCliApi):
        def list_inventory(self):
            raise ApiClientError("API returned HTTP 503: unavailable")

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["list"], client=FailingApi())

    assert exit_code == 1
    assert "HTTP 503" in error_output.getvalue()
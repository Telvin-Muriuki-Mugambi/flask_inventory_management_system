import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiClientError(Exception):
    pass


class InventoryApiClient:
    def __init__(self, base_url="http://127.0.0.1:5000", timeout=10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_inventory(self):
        return self._request("GET", "/inventory")

    def get_inventory_item(self, item_id):
        return self._request("GET", f"/inventory/{item_id}")

    def add_inventory_item(self, item):
        return self._request("POST", "/inventory", item)

    def update_inventory_item(self, item_id, changes):
        return self._request("PATCH", f"/inventory/{item_id}", changes)

    def delete_inventory_item(self, item_id):
        return self._request("DELETE", f"/inventory/{item_id}")

    def lookup_barcode(self, barcode):
        return self._request("GET", f"/products/barcode/{barcode}")

    def search_products(self, name):
        query = urlencode({"name": name})
        return self._request("GET", f"/products/search?{query}")

    def _request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"

        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                response_body = response.read()
                if not response_body:
                    return None
                return json.loads(response_body.decode("utf-8"))
        except HTTPError as error:
            message = self._error_message(error)
            raise ApiClientError(f"API returned HTTP {error.code}: {message}") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ApiClientError(f"Could not communicate with the API: {error}") from error

    @staticmethod
    def _error_message(error):
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
            return error.reason or "Request failed."
        if isinstance(payload, dict):
            return payload.get("error", "Request failed.")
        return "Request failed."
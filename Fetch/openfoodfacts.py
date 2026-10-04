import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class OpenFoodFactsError(Exception):
    pass


class OpenFoodFactsClient:
    PRODUCT_API_URL = "https://world.openfoodfacts.org/api/v3/product"
    SEARCH_API_URL = "https://search.openfoodfacts.org/search"
    PRODUCT_FIELDS = "code,product_name,brands,quantity,image_url,categories"
    USER_AGENT = "InventoryManagementSystem/1.0"

    def __init__(self, timeout=5):
        self.timeout = timeout

    def get_by_barcode(self, barcode):
        fields = urlencode({"fields": self.PRODUCT_FIELDS})
        url = f"{self.PRODUCT_API_URL}/{quote(barcode, safe='')}.json?{fields}"
        response = self._get_json(url)

        if response.get("status") != "success":
            return None

        product = response.get("product")
        if not isinstance(product, dict):
            return None
        return self._normalize_product(product, barcode)

    def search_by_name(self, name, limit=10):
        query = urlencode(
            {
                "q": name,
                "page_size": limit,
                "fields": self.PRODUCT_FIELDS,
                "langs": "en",
            }
        )
        response = self._get_json(f"{self.SEARCH_API_URL}?{query}")
        hits = response.get("hits")
        if not isinstance(hits, list):
            raise OpenFoodFactsError("Open Food Facts returned an invalid search response.")

        return [
            self._normalize_product(hit)
            for hit in hits
            if isinstance(hit, dict)
        ]

    def _get_json(self, url):
        request = Request(url, headers={"User-Agent": self.USER_AGENT})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise OpenFoodFactsError("Open Food Facts request failed.") from error

    @staticmethod
    def _normalize_product(product, barcode=None):
        return {
            "barcode": product.get("code", barcode),
            "name": product.get("product_name") or product.get("product_name_en"),
            "brands": product.get("brands"),
            "quantity": product.get("quantity"),
            "image_url": product.get("image_url"),
            "categories": product.get("categories"),
        }
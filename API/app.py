from flask import Flask, jsonify, request, url_for

from Fetch import OpenFoodFactsClient, OpenFoodFactsError
from API.inventory import InventoryStore


ITEM_FIELDS = {"name", "quantity", "price", "barcode"}
REQUIRED_FIELDS = {"name", "quantity", "price"}


def _validate_item_payload(payload, partial=False):
    if not isinstance(payload, dict):
        return "Request body must be a JSON object."

    unknown_fields = set(payload) - ITEM_FIELDS
    if unknown_fields:
        return f"Unsupported fields: {', '.join(sorted(unknown_fields))}."

    if partial and not payload:
        return "At least one item field is required."

    missing_fields = REQUIRED_FIELDS - set(payload)
    if not partial and missing_fields:
        return f"Missing required fields: {', '.join(sorted(missing_fields))}."

    if "name" in payload and (
        not isinstance(payload["name"], str) or not payload["name"].strip()
    ):
        return "Name must be a non-empty string."

    if "quantity" in payload and (
        isinstance(payload["quantity"], bool)
        or not isinstance(payload["quantity"], int)
        or payload["quantity"] < 0
    ):
        return "Quantity must be a non-negative integer."

    if "price" in payload and (
        isinstance(payload["price"], bool)
        or not isinstance(payload["price"], (int, float))
        or payload["price"] < 0
    ):
        return "Price must be a non-negative number."

    if "barcode" in payload and payload["barcode"] is not None and not isinstance(
        payload["barcode"], str
    ):
        return "Barcode must be a string or null."

    return None


def create_app(store=None, product_client=None):
    app = Flask(__name__)
    inventory = store if store is not None else InventoryStore()
    products = product_client if product_client is not None else OpenFoodFactsClient()

    @app.get("/inventory")
    def list_inventory():
        return jsonify(inventory.list_items())

    @app.get("/inventory/<int:item_id>")
    def get_inventory_item(item_id):
        item = inventory.get_item(item_id)
        if item is None:
            return jsonify({"error": "Inventory item not found."}), 404
        return jsonify(item)

    @app.get("/products/barcode/<barcode>")
    def lookup_product_by_barcode(barcode):
        if not barcode.isascii() or not barcode.isdigit():
            return jsonify({"error": "Barcode must contain only digits."}), 400

        try:
            product = products.get_by_barcode(barcode)
        except OpenFoodFactsError:
            return jsonify({"error": "Open Food Facts service is unavailable."}), 502

        if product is None:
            return jsonify({"error": "Product not found."}), 404
        return jsonify({"source": "Open Food Facts", "product": product})

    @app.get("/products/search")
    def search_products_by_name():
        name = request.args.get("name", "").strip()
        if not name:
            return jsonify({"error": "A non-empty name query is required."}), 400

        try:
            matches = products.search_by_name(name)
        except OpenFoodFactsError:
            return jsonify({"error": "Open Food Facts service is unavailable."}), 502

        return jsonify(
            {
                "source": "Open Food Facts",
                "count": len(matches),
                "products": matches,
            }
        )

    @app.post("/inventory")
    def create_inventory_item():
        payload = request.get_json(silent=True)
        error = _validate_item_payload(payload)
        if error:
            return jsonify({"error": error}), 400

        item_data = {field: payload.get(field) for field in ITEM_FIELDS}
        item = inventory.add_item(item_data)
        response = jsonify(item)
        response.status_code = 201
        response.headers["Location"] = url_for(
            "get_inventory_item", item_id=item["id"]
        )
        return response

    @app.patch("/inventory/<int:item_id>")
    def update_inventory_item(item_id):
        payload = request.get_json(silent=True)
        error = _validate_item_payload(payload, partial=True)
        if error:
            return jsonify({"error": error}), 400

        item = inventory.update_item(item_id, payload)
        if item is None:
            return jsonify({"error": "Inventory item not found."}), 404
        return jsonify(item)

    @app.delete("/inventory/<int:item_id>")
    def delete_inventory_item(item_id):
        if not inventory.delete_item(item_id):
            return jsonify({"error": "Inventory item not found."}), 404
        return "", 204

    return app